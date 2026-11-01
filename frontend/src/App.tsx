import React, { useState, useEffect } from 'react';
import { Sidebar, NavTab } from './components/Sidebar';
import { Header } from './components/Header';
import { QuickGuideModal } from './components/QuickGuideModal';
import { OverviewPage } from './pages/OverviewPage';
import { LiveMapPage } from './pages/LiveMapPage';
import { ForecastingPage } from './pages/ForecastingPage';
import { SpatialPage } from './pages/SpatialPage';
import { PropagationPage } from './pages/PropagationPage';
import { DiwaliSimulatorPage } from './pages/DiwaliSimulatorPage';
import { RecoveryPage } from './pages/RecoveryPage';
import { ScenarioComparisonPage } from './pages/ScenarioComparisonPage';
import { ModelIntelligencePage } from './pages/ModelIntelligencePage';
import { apiClient } from './api/client';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<NavTab>('overview');
  const [apiHealthy, setApiHealthy] = useState<boolean>(true);
  const [lastSyncTime, setLastSyncTime] = useState<string>(new Date().toISOString());
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const [isGuideOpen, setIsGuideOpen] = useState<boolean>(false);

  // Dark / Light Theme State with LocalStorage persistence and system preference fallback
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('aeros_theme');
      if (saved === 'dark' || saved === 'light') return saved;
      if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        return 'dark';
      }
    }
    return 'light';
  });

  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    localStorage.setItem('aeros_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  const checkHealth = async () => {
    try {
      setIsRefreshing(true);
      await apiClient.getSimulationHealth();
      setApiHealthy(true);
      setLastSyncTime(new Date().toISOString());
    } catch (e) {
      setApiHealthy(false);
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 30000); // 30s heartbeat
    return () => clearInterval(interval);
  }, []);

  const pageHeaders: Record<NavTab, { title: string; subtitle: string }> = {
    overview: {
      title: 'Air Quality Overview',
      subtitle: 'Live ambient air conditions, weather factors, and active monitoring network',
    },
    'live-map': {
      title: 'Environmental Map',
      subtitle: 'Continuous physical stations and spatial pollution estimates across Delhi NCR',
    },
    forecasting: {
      title: 'Air Quality Forecasts',
      subtitle: 'Hourly predictions from 1 to 72 hours ahead with 90% confidence intervals',
    },
    spatial: {
      title: 'Neighbourhood Estimates',
      subtitle: 'Estimating air quality at unmonitored locations using graph spatial modeling',
    },
    propagation: {
      title: 'Pollution Propagation',
      subtitle: 'Simulating wind transport and particulate diffusion across the airshed',
    },
    simulator: {
      title: 'What-if Scenarios',
      subtitle: 'Evaluating the air quality impact of emission changes and mitigation policies',
    },
    recovery: {
      title: 'Air Quality Recovery',
      subtitle: 'Projected hours required to return to clean air thresholds after pollution events',
    },
    comparison: {
      title: 'Scenario Comparison',
      subtitle: 'Side-by-side benchmark of policy scenarios and estimated pollution reductions',
    },
    models: {
      title: 'Model Intelligence',
      subtitle: 'Validation metrics, dataset specifications, and model architecture documentation',
    },
  };

  const currentHeader = pageHeaders[currentTab];

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#F7F7F3] text-charcoal">
      {/* Navigation Sidebar */}
      <Sidebar
        currentTab={currentTab}
        onSelectTab={setCurrentTab}
        apiHealthy={apiHealthy}
        onOpenGuide={() => setIsGuideOpen(true)}
        theme={theme}
        onToggleTheme={toggleTheme}
      />

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <Header
          title={currentHeader.title}
          subtitle={currentHeader.subtitle}
          onRefresh={checkHealth}
          onOpenGuide={() => setIsGuideOpen(true)}
          isLoading={isRefreshing}
          lastUpdated={lastSyncTime}
          theme={theme}
          onToggleTheme={toggleTheme}
        />

        <main className="flex-1 overflow-y-auto p-8">
          <div className="mx-auto max-w-7xl">
            {currentTab === 'overview' && <OverviewPage />}
            {currentTab === 'live-map' && <LiveMapPage />}
            {currentTab === 'forecasting' && <ForecastingPage />}
            {currentTab === 'spatial' && <SpatialPage />}
            {currentTab === 'propagation' && <PropagationPage />}
            {currentTab === 'simulator' && <DiwaliSimulatorPage />}
            {currentTab === 'recovery' && <RecoveryPage />}
            {currentTab === 'comparison' && <ScenarioComparisonPage />}
            {currentTab === 'models' && <ModelIntelligencePage />}
          </div>
        </main>
      </div>

      {/* Interactive Quick Guide Modal */}
      <QuickGuideModal
        isOpen={isGuideOpen}
        onClose={() => setIsGuideOpen(false)}
        onSelectTab={(tab) => setCurrentTab(tab)}
      />
    </div>
  );
};

export default App;
