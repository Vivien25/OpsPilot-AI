import { useState } from "react";
import UploadPage from "./pages/UploadPage";
import WarehouseMapPage from "./pages/WarehouseMapPage";

function App() {
  const [activePage, setActivePage] = useState("map");

  if (activePage === "analysis") {
    return <UploadPage activePage={activePage} onNavigate={setActivePage} />;
  }

  return <WarehouseMapPage activePage="map" onNavigate={setActivePage} />;
}

export default App;
