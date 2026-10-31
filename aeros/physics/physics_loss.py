"""Physics-Informed Atmospheric Transport Loss Functions for AEROS.

Enforces physical consistency in deep neural network predictions by penalizing
residuals of the 2D Advection-Diffusion-Reaction PDE, unphysical negative concentrations,
and excessive mass imbalances.
"""

from typing import Dict, Optional, Tuple
import torch
import torch.nn as nn
import torch.nn.functional as F


class PhysicsInformedTransportLoss(nn.Module):
    """Computes physics loss residuals for spatiotemporal concentration predictions."""

    def __init__(
        self,
        dx_km: float = 5.5,
        dy_km: float = 5.5,
        dt_h: float = 1.0,
        default_k_diff: float = 12.0,  # km²/h
        lambda_pde: float = 0.1,
        lambda_nonneg: float = 1.0,
        lambda_mass: float = 0.05,
    ):
        super().__init__()
        self.dx = dx_km
        self.dy = dy_km
        self.dt = dt_h
        self.default_k_diff = default_k_diff
        self.lambda_pde = lambda_pde
        self.lambda_nonneg = lambda_nonneg
        self.lambda_mass = lambda_mass

    def forward(
        self,
        pred_c: torch.Tensor,
        u_kmh: torch.Tensor,
        v_kmh: torch.Tensor,
        sources: Optional[torch.Tensor] = None,
        sinks_lambda: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        """Computes combined physics loss for a 4D concentration tensor [Batch, Time, Height, Width].
        
        Args:
            pred_c: [B, T, H, W] tensor of predicted pollutant concentration (e.g. PM2.5).
            u_kmh: [B, T] or scalar tensor of zonal wind velocity (km/h).
            v_kmh: [B, T] or scalar tensor of meridional wind velocity (km/h).
            sources: Optional [B, T, H, W] emission source term.
            sinks_lambda: Optional [B, T, H, W] sink removal rate (1/h).
            
        Returns:
            (total_physics_loss, component_metrics_dict)
        """
        B, T, H, W = pred_c.shape

        # 1. Non-negativity constraint: penalize negative concentrations
        nonneg_loss = torch.mean(F.relu(-pred_c) ** 2)

        if T < 2:
            # Need at least two time steps to evaluate temporal derivative dC/dt
            total_loss = self.lambda_nonneg * nonneg_loss
            return total_loss, {
                "loss_pde": 0.0,
                "loss_nonneg": float(nonneg_loss.item()),
                "loss_total_physics": float(total_loss.item()),
            }

        # 2. Time derivative dC/dt: [B, T-1, H, W]
        dc_dt = (pred_c[:, 1:, :, :] - pred_c[:, :-1, :, :]) / self.dt

        # Midpoint concentration for spatial terms: [B, T-1, H, W]
        c_mid = 0.5 * (pred_c[:, 1:, :, :] + pred_c[:, :-1, :, :])

        # 3. Spatial Gradients (Advection) using central differencing on interior
        # dC/dx: along width (W, x-axis)
        dc_dx = (c_mid[:, :, :, 2:] - c_mid[:, :, :, :-2]) / (2.0 * self.dx)
        # dC/dy: along height (H, y-axis)
        dc_dy = (c_mid[:, :, 2:, :] - c_mid[:, :, :-2, :]) / (2.0 * self.dy)

        # 4. Spatial Laplacians (Diffusion)
        d2c_dx2 = (c_mid[:, :, :, 2:] - 2.0 * c_mid[:, :, :, 1:-1] + c_mid[:, :, :, :-2]) / (self.dx**2)
        d2c_dy2 = (c_mid[:, :, 2:, :] - 2.0 * c_mid[:, :, 1:-1, :] + c_mid[:, :, :-2, :]) / (self.dy**2)

        # Align shapes to interior domain [B, T-1, H-2, W-2]
        dc_dt_int = dc_dt[:, :, 1:-1, 1:-1]
        c_mid_int = c_mid[:, :, 1:-1, 1:-1]
        dc_dx_int = dc_dx[:, :, 1:-1, :]
        dc_dy_int = dc_dy[:, :, :, 1:-1]
        d2c_dx2_int = d2c_dx2[:, :, 1:-1, :]
        d2c_dy2_int = d2c_dy2[:, :, :, 1:-1]

        # Reshape wind components if needed
        if u_kmh.dim() == 2:
            u_exp = u_kmh[:, :-1, None, None]
            v_exp = v_kmh[:, :-1, None, None]
        elif u_kmh.dim() == 0:
            u_exp = u_kmh
            v_exp = v_kmh
        else:
            u_exp = u_kmh
            v_exp = v_kmh

        # Advective term: u * dC/dx + v * dC/dy
        advection_term = u_exp * dc_dx_int + v_exp * dc_dy_int

        # Diffusive term: K * (d²C/dx² + d²C/dy²)
        diffusion_term = self.default_k_diff * (d2c_dx2_int + d2c_dy2_int)

        # Source and sink terms on interior
        s_int = (
            sources[:, :-1, 1:-1, 1:-1]
            if sources is not None
            else torch.zeros_like(dc_dt_int)
        )
        l_int = (
            sinks_lambda[:, :-1, 1:-1, 1:-1] * c_mid_int
            if sinks_lambda is not None
            else torch.zeros_like(dc_dt_int)
        )

        # PDE Residual: R = dC/dt + u·∇C - K·∇²C - S + L
        pde_residual = dc_dt_int + advection_term - diffusion_term - s_int + l_int
        loss_pde = torch.mean(pde_residual**2)

        # 5. Mass Conservation Constraint
        # Total mass over spatial domain at each timestep
        spatial_mass = torch.sum(pred_c, dim=[-2, -1]) * self.dx * self.dy  # [B, T]
        mass_rate = (spatial_mass[:, 1:] - spatial_mass[:, :-1]) / self.dt
        loss_mass = torch.mean(mass_rate**2)  # In closed or large domain, mass variation should be smooth

        # Combined Loss
        total_loss = (
            self.lambda_pde * loss_pde
            + self.lambda_nonneg * nonneg_loss
            + self.lambda_mass * loss_mass
        )

        metrics = {
            "loss_pde": float(loss_pde.item()),
            "loss_nonneg": float(nonneg_loss.item()),
            "loss_mass": float(loss_mass.item()),
            "loss_total_physics": float(total_loss.item()),
        }

        return total_loss, metrics
