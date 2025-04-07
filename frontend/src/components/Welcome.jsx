import React from "react";
import { Card, Typography, Button, Box } from "@mui/material";
import { useNavigate } from "react-router-dom";
import { styled } from "@mui/material/styles";

const Background = styled(Box)({
  height: "100vh",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  background: `url('https://venturebeat.com/wp-content/uploads/2024/05/nuneybits_A_split-screen_image_depicting_two_contrasting_interv_b0e9e4f5-d132-4250-9c46-ce9a02dfb440-transformed.webp?w=750') no-repeat center center/cover`,
});

const StyledCard = styled(Card)({
  width: "90%",
  maxWidth: "500px",
  padding: "30px",
  textAlign: "center",
  background: "rgba(255, 255, 255, 0.2)",
  backdropFilter: "blur(10px)",
  borderRadius: "20px",
  boxShadow: "0px 10px 30px rgba(0,0,0,0.3)",
  color: "white",
});

const Welcome = () => {
  const navigate = useNavigate();

  return (
    <Background>
      <StyledCard>
        <Typography variant="h4" gutterBottom>
          Welcome to AI Portal!
        </Typography>
        <Typography variant="body1" sx={{ color: "#ddd", marginBottom: "20px" }}>
          Explore AI-powered mock interviews and enhance your skills.
        </Typography>
        <Button
  variant="contained"
  sx={{
    backgroundColor: "#0077FF",
    color: "white",
    fontSize: "16px",
    padding: "12px 24px",
    borderRadius: "10px",
    transition: "0.3s",
    "&:hover": { backgroundColor: "#0057CC", transform: "scale(1.05)" },
  }}
  onClick={() => navigate("/signin")} // Changed from "/mock-interview"
>
  Get Started
</Button>
      </StyledCard>
    </Background>
  );
};

export default Welcome;
