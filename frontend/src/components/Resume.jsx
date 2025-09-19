// Resume.jsx
import React, { useState } from "react";
import {
  Button,
  Container,
  Typography,
  Card,
  Box,
  Input,
} from "@mui/material";
import { useNavigate } from "react-router-dom";
import { styled } from "@mui/material/styles";

// Styled Background (same as MockInterview.jsx)
const Background = styled(Box)({
  position: "fixed",
  top: 0,
  left: 0,
  width: "100%",
  height: "100%",
  backgroundImage: `url('/bg.jpg')`,
  backgroundSize: "cover",
  backgroundPosition: "center",
  backgroundRepeat: "no-repeat",
  zIndex: -1,
  "&::before": {
    content: '""',
    position: "absolute",
    top: 0,
    left: 0,
    width: "100%",
    height: "100%",
    backgroundColor: "rgba(0, 0, 0, 0.5)",
    zIndex: 1,
  },
});

const ContentWrapper = styled(Box)({
  position: "relative",
  zIndex: 2,
  minHeight: "100vh",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  padding: "20px",
});

const Resume = () => {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleNext = () => {
    if (!file) {
      alert("Please upload your resume first.");
      return;
    }
    navigate("/mock-interview", { state: { resume: file } });
  };

  return (
    <>
      <Background />
      <ContentWrapper>
        <Container maxWidth="sm">
          <Card
            sx={{
              p: 4,
              backgroundColor: "rgba(255, 255, 255, 0.1)",
              borderRadius: 3,
              boxShadow: 3,
              backdropFilter: "blur(10px)",
              color: "white",
              textAlign: "center",
            }}
          >
            <Typography variant="h4" gutterBottom sx={{ fontWeight: "bold" }}>
              Upload Your Resume
            </Typography>
            <Typography variant="subtitle1" sx={{ mb: 2 }}>
              Supported formats: PDF, DOCX, TXT
            </Typography>

            <Box sx={{ mb: 3 }}>
              <Input
                type="file"
                onChange={handleFileChange}
                inputProps={{ accept: ".pdf,.docx,.txt" }}
                sx={{ color: "white" }}
              />
            </Box>

            {file && (
              <Typography variant="body2" sx={{ mb: 2, fontStyle: "italic" }}>
                Selected: {file.name}
              </Typography>
            )}

            <Button
              variant="contained"
              onClick={handleNext}
              sx={{
                backgroundColor: "#00c6ff",
                "&:hover": { backgroundColor: "#0072ff" },
              }}
            >
              Next
            </Button>
          </Card>
        </Container>
      </ContentWrapper>
    </>
  );
};

export default Resume;
