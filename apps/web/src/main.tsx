import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App } from "./App";
import { Setup } from "./Setup";
import "./styles.css";

const root = document.getElementById("root");

if (!root) {
  throw new Error("Kinward root element is missing");
}

createRoot(root).render(
  <StrictMode>
    {window.location.pathname === "/setup" ? <Setup /> : <App />}
  </StrictMode>,
);
