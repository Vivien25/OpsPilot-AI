import { useState } from "react";
import InvestigationPage from "./pages/InvestigationPage";
import LandingPage from "./pages/LandingPage";
import OperationsDashboardPage from "./pages/OperationsDashboardPage";
import WarehouseMapPage from "./pages/WarehouseMapPage";

function App() {
  const [activePage, setActivePage] = useState("landing");

  if (activePage === "landing") {
    return <LandingPage onNavigate={setActivePage} />;
  }

  if (activePage === "dashboard") {
    return <OperationsDashboardPage activePage={activePage} onNavigate={setActivePage} />;
  }

  if (activePage === "investigation") {
    return <InvestigationPage activePage={activePage} onNavigate={setActivePage} />;
  }

  return <WarehouseMapPage activePage="map" onNavigate={setActivePage} />;
}

export default App;
