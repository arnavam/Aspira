import * as React from "react";
import {
  Box,
  Button,
  CssBaseline,
  FormControl,
  FormLabel,
  TextField,
  Typography,
  Card as MuiCard,
  Stack,
  Snackbar,
  Alert,
  CircularProgress,
} from "@mui/material";
import { styled } from "@mui/material/styles";
import { useNavigate } from "react-router-dom";
import { 
  getAuth, 
  createUserWithEmailAndPassword, 
  signInWithEmailAndPassword 
} from "firebase/auth";
import { initializeApp } from "firebase/app";

// Replace with your actual Firebase config
const firebaseConfig = {
  apiKey: "AIzaSyALXWOgThlxfwXPdLCHNBBfb4BaB6Wqt7A",
  authDomain: "aspira1.firebaseapp.com",
  projectId: "aspira1",
  storageBucket: "aspira1.firebasestorage.app",
  messagingSenderId: "114286394187",
  appId: "1:114286394187:web:0c37d08e3b988cce04c6ce"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

const Card = styled(MuiCard)(({ theme }) => ({
  display: "flex",
  flexDirection: "column",
  alignSelf: "center",
  width: "100%",
  padding: theme.spacing(4),
  gap: theme.spacing(2),
  margin: "auto",
  [theme.breakpoints.up("sm")]: {
    maxWidth: "450px",
  },
  backgroundColor: "rgba(0, 0, 51, 0.9)",
  color: "white",
  boxShadow: "0px 10px 30px rgba(0,0,0,0.3)",
}));

const SignInContainer = styled(Stack)(({ theme }) => ({
  position: "fixed",
  top: 0,
  left: 0,
  width: "100vw",
  height: "100vh",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  padding: theme.spacing(2),
  background: `url('bg.jpg') no-repeat center center/cover`,
}));

export default function SignIn({ setIsAuthenticated }) {
  const navigate = useNavigate();
  const [isSignUp, setIsSignUp] = React.useState(false);
  const [formData, setFormData] = React.useState({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [errors, setErrors] = React.useState({});
  const [authError, setAuthError] = React.useState(null);
  const [isLoading, setIsLoading] = React.useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    if (errors[e.target.name]) {
      setErrors({ ...errors, [e.target.name]: "" });
    }
  };

  const validateInputs = () => {
    let isValid = true;
    let newErrors = {};

    if (isSignUp && !formData.username.trim()) {
      newErrors.username = "Username is required.";
      isValid = false;
    }

    if (!formData.email || !/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = "Enter a valid email address.";
      isValid = false;
    }

    if (!formData.password || formData.password.length < 6) {
      newErrors.password = "Password must be at least 6 characters.";
      isValid = false;
    }

    if (isSignUp && formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = "Passwords do not match.";
      isValid = false;
    }

    setErrors(newErrors);
    return isValid;
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setAuthError(null);
    
    if (!validateInputs()) return;

    setIsLoading(true);
    
    try {
      console.log("Attempting", isSignUp ? "sign up" : "sign in");
      
      if (isSignUp) {
        const userCredential = await createUserWithEmailAndPassword(
          auth,
          formData.email,
          formData.password
        );
        console.log("User created:", userCredential.user);
        localStorage.setItem("username", formData.username);
        localStorage.setItem("email", formData.email);
      } else {
        const userCredential = await signInWithEmailAndPassword(
          auth,
          formData.email,
          formData.password
        );
        console.log("User signed in:", userCredential.user);
      }
      
      localStorage.setItem("isLoggedIn", "true");
      setIsAuthenticated(true);
      navigate("/u");
    } catch (error) {
      console.error("Authentication error:", error);
      let errorMessage = "Authentication failed";
      
      switch(error.code) {
        case "auth/email-already-in-use":
          errorMessage = "Email already in use";
          break;
        case "auth/invalid-email":
          errorMessage = "Invalid email address";
          break;
        case "auth/weak-password":
          errorMessage = "Password should be at least 6 characters";
          break;
        case "auth/user-not-found":
          errorMessage = "No user found with this email";
          break;
        case "auth/wrong-password":
          errorMessage = "Incorrect password";
          break;
        case "auth/network-request-failed":
          errorMessage = "Network error. Please check your connection";
          break;
        default:
          errorMessage = error.message;
      }
      
      setAuthError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGuestAccess = () => {
    localStorage.setItem("username", "Guest");
    localStorage.setItem("isLoggedIn", "true");
    setIsAuthenticated(true);
    navigate("/home");
  };

  return (
    <>
      <CssBaseline />
      <SignInContainer>
        <Card variant="outlined">
          <Typography component="h1" variant="h4" sx={{ textAlign: "center" }}>
            {isSignUp ? "Create an Account" : "Sign In"}
          </Typography>
          <Box component="form" onSubmit={handleSubmit} noValidate>
            {isSignUp && (
              <FormControl fullWidth sx={{ mb: 2 }}>
                <FormLabel htmlFor="username" sx={{ color: "#ffffff" }}>
                  Username
                </FormLabel>
                <TextField
                  error={!!errors.username}
                  helperText={errors.username}
                  name="username"
                  id="username"
                  value={formData.username}
                  onChange={handleChange}
                  fullWidth
                  variant="outlined"
                  sx={{
                    input: { color: "white" },
                    "& .MuiOutlinedInput-root": {
                      "& fieldset": { borderColor: "white" },
                      "&:hover fieldset": { borderColor: "#66a3ff" },
                    },
                  }}
                />
              </FormControl>
            )}
            
            <FormControl fullWidth sx={{ mb: 2 }}>
              <FormLabel htmlFor="email" sx={{ color: "#ffffff" }}>
                Email
              </FormLabel>
              <TextField
                error={!!errors.email}
                helperText={errors.email}
                name="email"
                id="email"
                type="email"
                value={formData.email}
                onChange={handleChange}
                required
                fullWidth
                variant="outlined"
                sx={{
                  input: { color: "white" },
                  "& .MuiOutlinedInput-root": {
                    "& fieldset": { borderColor: "white" },
                    "&:hover fieldset": { borderColor: "#66a3ff" },
                  },
                }}
              />
            </FormControl>
            
            <FormControl fullWidth sx={{ mb: 2 }}>
              <FormLabel htmlFor="password" sx={{ color: "#ffffff" }}>
                Password
              </FormLabel>
              <TextField
                error={!!errors.password}
                helperText={errors.password}
                name="password"
                id="password"
                type="password"
                value={formData.password}
                onChange={handleChange}
                required
                fullWidth
                variant="outlined"
                sx={{
                  input: { color: "white" },
                  "& .MuiOutlinedInput-root": {
                    "& fieldset": { borderColor: "white" },
                    "&:hover fieldset": { borderColor: "#66a3ff" },
                  },
                }}
              />
            </FormControl>
            
            {isSignUp && (
              <FormControl fullWidth sx={{ mb: 2 }}>
                <FormLabel htmlFor="confirmPassword" sx={{ color: "#ffffff" }}>
                  Confirm Password
                </FormLabel>
                <TextField
                  error={!!errors.confirmPassword}
                  helperText={errors.confirmPassword}
                  name="confirmPassword"
                  id="confirmPassword"
                  type="password"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  required
                  fullWidth
                  variant="outlined"
                  sx={{
                    input: { color: "white" },
                    "& .MuiOutlinedInput-root": {
                      "& fieldset": { borderColor: "white" },
                      "&:hover fieldset": { borderColor: "#66a3ff" },
                    },
                  }}
                />
              </FormControl>
            )}
            
            <Button 
              type="submit" 
              fullWidth 
              variant="contained" 
              disabled={isLoading}
              sx={{ 
                mt: 2, 
                mb: 1,
                backgroundColor: "#2196f3", 
                '&:hover': { 
                  backgroundColor: "#1976d2" 
                },
                height: "48px"
              }}
            >
              {isLoading ? (
                <CircularProgress size={24} color="inherit" />
              ) : isSignUp ? (
                "Create Account"
              ) : (
                "Sign In"
              )}
            </Button>

            <Button 
              onClick={() => setIsSignUp(!isSignUp)} 
              fullWidth 
              sx={{ 
                color: "#90caf9",
                textTransform: 'none'
              }}
            >
              {isSignUp ? (
                "Already have an account? Sign In"
              ) : (
                "Don't have an account? Create one"
              )}
            </Button>
            
            <Button 
              onClick={handleGuestAccess}
              fullWidth 
              variant="outlined"
              sx={{ 
                mt: 1,
                color: "#90caf9",
                borderColor: "#90caf9",
                '&:hover': {
                  borderColor: "#42a5f5",
                  backgroundColor: "rgba(144, 202, 249, 0.08)"
                }
              }}
            >
              Continue as Guest
            </Button>
          </Box>
        </Card>
        
        <Snackbar
          open={!!authError}
          autoHideDuration={6000}
          onClose={() => setAuthError(null)}
          anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        >
          <Alert 
            onClose={() => setAuthError(null)} 
            severity="error" 
            sx={{ width: '100%' }}
          >
            {authError}
          </Alert>
        </Snackbar>
      </SignInContainer>
    </>
  );
}