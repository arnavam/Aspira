import { Routes, Route, Navigate } from "react-router-dom";
import { useState } from "react";
import SignIn from "./components/Signin";
import Navbar from "./components/Navbar";
import View from "./components/View";
import MockInterview from "./components/MockInterview";
import Interface from "./components/Interface";
import Home from "./components/Home";
import Rank from "./components/Rank";
import Welcome from "./components/Welcome";

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(() => {
    return localStorage.getItem("isLoggedIn") === "true";
  });

  return (
    <>
      <Navbar isAuthenticated={isAuthenticated} setIsAuthenticated={setIsAuthenticated} />
      <Routes>
        {/* Default Landing Page - Welcome */}
        <Route path="/" element={<Welcome />} />

        {/* Sign In Page */}
        <Route
          path="/signin"
          element={
            isAuthenticated ? <Navigate to="/home" replace /> : <SignIn setIsAuthenticated={setIsAuthenticated} />
          }
        />

        {/* Home Page */}
        <Route
          path="/home"
          element={isAuthenticated ? <Home /> : <Navigate to="/signin" replace />}
        />

        {/* Mock Interview */}
        <Route
          path="/mock-interview"
          element={isAuthenticated ? <MockInterview /> : <Navigate to="/signin" replace />}
        />

        {/* AI Interface */}
        <Route
          path="/interface"
          element={isAuthenticated ? <Interface /> : <Navigate to="/signin" replace />}
        />

        {/* Rank Page */}
        <Route
          path="/rank"
          element={isAuthenticated ? <Rank /> : <Navigate to="/signin" replace />}
        />

        {/* View Page */}
        <Route path="/view" element={<View />} />

        {/* Redirect unknown routes to Welcome */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}

export default App;
