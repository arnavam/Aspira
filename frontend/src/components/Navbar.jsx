import React, { useState } from "react";
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  IconButton,
  Menu,
  MenuItem,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import { useNavigate, useLocation } from "react-router-dom";
import { EmojiEvents, Home, ExitToApp, Menu as MenuIcon, Share } from "@mui/icons-material";

const Navbar = ({ isAuthenticated, setIsAuthenticated }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));
  const navigate = useNavigate();
  const location = useLocation(); // Get the current route
  const [anchorEl, setAnchorEl] = useState(null);

  // Hide Navbar on these pages
  const hideNavbarRoutes = ["/", "/signin"];
  if (hideNavbarRoutes.includes(location.pathname)) {
    return null;
  }

  const handleMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleNavigation = (path) => {
    navigate(path);
    handleMenuClose();
  };

  const handleLogout = () => {
    localStorage.removeItem("isLoggedIn");
    localStorage.removeItem("username");
    setIsAuthenticated(false);
    navigate("/signin");
    handleMenuClose();
  };

  const handleShare = () => {
    if (navigator.share) {
      navigator
        .share({
          title: "ASPIRA",
          text: "Check out this amazing platform!",
          url: window.location.href,
        })
        .then(() => console.log("Successful share"))
        .catch((error) => console.log("Error sharing", error));
    } else {
      navigator.clipboard
        .writeText(window.location.href)
        .then(() => alert("Link copied to clipboard!"))
        .catch(() => alert("Failed to copy link to clipboard."));
    }
  };

  return (
    <AppBar
      position="fixed"
      sx={{
        background: "linear-gradient(45deg, #1a237e 30%, #0d47a1 90%)",
        boxShadow: "0 3px 5px 2px rgba(0, 0, 0, .3)",
      }}
    >
      <Toolbar>
        <Typography
          variant="h6"
          sx={{
            flexGrow: 1,
            fontWeight: "bold",
            background: "linear-gradient(45deg, #00c6ff 30%, #0072ff 90%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
          }}
        >
          ASPIRA
        </Typography>

        {isAuthenticated && (
          <Box sx={{ display: "flex", alignItems: "center" }}>
            <IconButton color="inherit" onClick={handleShare} aria-label="share" sx={{ mx: 1 }}>
              <Share />
            </IconButton>

            {isMobile ? (
              <>
                <IconButton color="inherit" onClick={handleMenuOpen} aria-label="navigation menu">
                  <MenuIcon />
                </IconButton>
                <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={handleMenuClose}>
                  <MenuItem onClick={() => handleNavigation("/home")}>
                    <Home sx={{ mr: 1 }} /> Home
                  </MenuItem>
                  <MenuItem onClick={() => handleNavigation("/rank")}>
                    <EmojiEvents sx={{ mr: 1 }} /> Rankings
                  </MenuItem>
                  <MenuItem onClick={handleLogout}>
                    <ExitToApp sx={{ mr: 1 }} /> Logout
                  </MenuItem>
                </Menu>
              </>
            ) : (
              <>
                <Button
                  color="inherit"
                  onClick={() => handleNavigation("/home")}
                  startIcon={<Home />}
                  sx={{
                    mx: 1,
                    "&:hover": {
                      background: "rgba(255,255,255,0.1)",
                    },
                  }}
                >
                  Home
                </Button>
                <Button
                  color="inherit"
                  onClick={() => handleNavigation("/rank")}
                  startIcon={<EmojiEvents />}
                  sx={{
                    mx: 1,
                    "&:hover": {
                      background: "rgba(255,255,255,0.1)",
                    },
                  }}
                >
                  Rankings
                </Button>
                <Button
                  color="inherit"
                  onClick={handleLogout}
                  startIcon={<ExitToApp />}
                  sx={{
                    mx: 1,
                    "&:hover": {
                      background: "rgba(255,255,255,0.1)",
                    },
                  }}
                >
                  Logout
                </Button>
              </>
            )}
          </Box>
        )}
      </Toolbar>
    </AppBar>
  );
};

export default Navbar;
