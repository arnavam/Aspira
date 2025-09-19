import React, { useState, useEffect } from "react";
import {
  Button,
  Container,
  Typography,
  TextField,
  Card,
  Box,
} from "@mui/material";
import { useLocation, useNavigate } from "react-router-dom";
import { styled } from "@mui/material/styles";

// Styled Components
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

// Sample Interview Questions
const questions = ["Can you tell more about your preffered job?"];

const MockInterview = () => {
  const navigate = useNavigate();
  const [questionIndex, setQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState(Array(questions.length).fill(""));
  const [timeLeft, setTimeLeft] = useState(180);
  const [param_ans, setParam_ans] = useState("");
  const { state } = useLocation();
  // console.log(state?.resume);

  // Authentication Check
  useEffect(() => {
    if (localStorage.getItem("isLoggedIn") !== "true") {
      navigate("/signin");
    }
  }, [navigate]);

  // Timer Logic
  useEffect(() => {
    if (timeLeft === 0) {
      alert("Time's up! Moving to the next question.");
      handleNextQuestion();
      return;
    }

    const timer = setInterval(() => {
      setTimeLeft((prev) => prev - 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [timeLeft, questionIndex]);

  // Reset Timer
  useEffect(() => {
    setTimeLeft(180);
  }, [questionIndex]);

  // Question Navigation
  const handleNextQuestion = () => {
    if (questionIndex < questions.length - 1) {
      setQuestionIndex(questionIndex + 1);
    } else {
      alert("Interview Completed! Redirecting to AI Interface...");
      // navigate("/interface", { state: param_ans });
      navigate("/interface", { state: { answers: param_ans, resume: state?.resume } });
      // console.log(param_ans)
      // console.log(state)
    }
  };

  const handlePreviousQuestion = () => {
    if (questionIndex > 0) {
      setQuestionIndex(questionIndex - 1);
    }
  };

  // Answer Handling
  const handleAnswerChange = (e) => {
    const updatedAnswers = [...answers];
    updatedAnswers[questionIndex] = e.target.value;
    setAnswers(updatedAnswers);
    setParam_ans(updatedAnswers);
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
            {/* Progress and Timer */}
            <Typography variant="subtitle1" sx={{ mb: 2 }}>
              Question {questionIndex + 1} of {questions.length}
            </Typography>
            <Typography variant="subtitle1" sx={{ mb: 2 }}>
              Time Left: {Math.floor(timeLeft / 60)}:
              {String(timeLeft % 60).padStart(2, "0")}
            </Typography>

            {/* Question Display */}
            <Typography variant="h4" gutterBottom sx={{ fontWeight: "bold" }}>
              Mock Interview
            </Typography>
            <Typography variant="h6" sx={{ mb: 2 }}>
              {questions[questionIndex]}
            </Typography>

            {/* Answer Input */}
            <TextField
              fullWidth
              multiline
              rows={3}
              value={answers[questionIndex]}
              onChange={handleAnswerChange}
              placeholder="Type your response here..."
              sx={{
                mb: 2,
                "& .MuiInputBase-input": {
                  color: "white",
                  "&::placeholder": {
                    color: "rgba(255, 255, 255, 0.7)",
                  },
                },
                "& .MuiOutlinedInput-root": {
                  "& fieldset": { borderColor: "white" },
                  "&:hover fieldset": { borderColor: "#66a3ff" },
                },
              }}
            />

            {/* Navigation Buttons */}
            <Box
              sx={{ display: "flex", justifyContent: "space-between", mt: 2 }}
            >
              <Button
                variant="outlined"
                onClick={handlePreviousQuestion}
                disabled={questionIndex === 0}
                sx={{
                  borderColor: "#00c6ff",
                  color: "#00c6ff",
                  "&:hover": { backgroundColor: "#00c6ff", color: "white" },
                }}
              >
                Back
              </Button>
              <Button
                variant="contained"
                onClick={handleNextQuestion}
                sx={{
                  backgroundColor: "#00c6ff",
                  "&:hover": { backgroundColor: "#0072ff" },
                }}
              >
                {questionIndex < questions.length - 1 ? "Next" : "Finish"}
              </Button>
            </Box>
          </Card>
        </Container>
      </ContentWrapper>
    </>
  );
};

export default MockInterview;
