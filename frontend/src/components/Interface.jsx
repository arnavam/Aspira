import React, { useState, useEffect, useRef } from "react";
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
import axios from "axios";
import * as pdfjsLib from "pdfjs-dist/legacy/build/pdf";
import mammoth from "mammoth";

// ✅ must be a string URL, not undefined or object
pdfjsLib.GlobalWorkerOptions.workerSrc = "/pdf.worker.min.mjs";

// ========== Question Banks ==========
const getBehavioralQuestions = () => [
  "Tell me about a time you faced a difficult challenge at work.",
  "Describe a situation where you had to work with a difficult team member.",
  "Give an example of how you handled a mistake you made at work.",
];

const getTechnicalQuestions = () => [
  "Explain your approach to solving complex technical problems.",
  "How do you stay updated with the latest technologies in your field?",
  "Describe a technical project you're particularly proud of.",
];

const getSituationalQuestions = () => [
  "What would you do if you disagreed with your manager's decision?",
  "How would you handle a tight deadline with multiple priorities?",
  "Describe how you would onboard a new team member.",
];

// ========== AI Response Generators ==========
const getEncouragingResponses = () => [
  "That's an excellent point! Could you elaborate further?",
  "Great answer! What other factors did you consider?",
  "Interesting perspective! How did this experience shape you?",
];

const getFollowUpResponses = () => [
  "What was the most challenging part of that situation?",
  "How would you approach this differently today?",
  "What key lessons did you learn from this experience?",
];

// ========== Speech Functions ==========
const initializeSpeech = () => {
  const synth = window.speechSynthesis;
  let recognition = null;

  if ("SpeechRecognition" in window || "webkitSpeechRecognition" in window) {
    recognition = new (window.SpeechRecognition ||
      window.webkitSpeechRecognition)();
    recognition.continuous = false;
    recognition.interimResults = false;
  }

  return { synth, recognition };
};

// const speakQuestion = (synth, question) => {
//   if (synth.speaking) {
//     synth.cancel();
//   }

//   const utterance = new SpeechSynthesisUtterance(question);
//   utterance.rate = 1.0;
//   utterance.pitch = 1.0;
//   synth.speak(utterance);
// };

// ========== Styled Components ==========
const Background = styled(Box)({
  position: "fixed",
  top: 0,
  left: 0,
  width: "100%",
  height: "100%",
  backgroundImage: `url('bg.jpg')`,
  backgroundSize: "cover",
  backgroundPosition: "center",
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
  overflow: "auto",
});

// ========== Main Component ==========
const Interface = () => {
  const navigate = useNavigate();
  const [questionIndex, setQuestionIndex] = useState(0);
  const [answer, setAnswer] = useState("");
  const [aiResponse, setAiResponse] = useState("");
  const [isListening, setIsListening] = useState(false);
  const [isInterviewStarted, setIsInterviewStarted] = useState(false);
  const [questionBank, setQuestionBank] = useState([]);
  const synthRef = useRef(null);
  const recognitionRef = useRef(null);
  const [questionget, setQuestionget] = useState("");
  const videoRef = useRef(null);
  const [videoname, setVideoname] = useState("/result_voice.mp4");
  const [resume, setResume] = useState("");
  const { state } = useLocation();
  // console.log(state)
  useEffect(() => {
  if (state?.resume) {
    fileToText(state.resume)
      .then((text) => {
        setResume(text); // schedules update
      })
      .catch((err) => console.error("Error reading file:", err));
  }
}, [state?.resume]);

// useEffect(() => {
//   if (resume) {
//     console.log("Resume state updated:", resume); // runs *after* setResume completes
//   }
// }, [resume]);

  // helper function
  const fileToText = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();

      // handle plain text
      if (file.type === "text/plain") {
        reader.onload = (e) => resolve(e.target.result);
        reader.onerror = reject;
        reader.readAsText(file);
      }
      // handle PDF
      else if (file.type === "application/pdf") {
        const readerForPdf = new FileReader();
        readerForPdf.onload = async (e) => {
          const typedarray = new Uint8Array(e.target.result);
          const pdf = await pdfjsLib.getDocument({ data: typedarray }).promise;
          let text = "";
          for (let i = 1; i <= pdf.numPages; i++) {
            const page = await pdf.getPage(i);
            const content = await page.getTextContent();
            const pageText = content.items.map((item) => item.str).join(" ");
            text += pageText + "\n";
          }
          resolve(text);
        };
        readerForPdf.onerror = reject;
        readerForPdf.readAsArrayBuffer(file);
      }
      // handle DOCX
      else if (
        file.type ===
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
      ) {
        import("mammoth").then((mammoth) => {
          const readerForDocx = new FileReader();
          readerForDocx.onload = async (e) => {
            try {
              const arrayBuffer = e.target.result;
              const result = await mammoth.extractRawText({ arrayBuffer });
              resolve(result.value);
            } catch (err) {
              reject(err);
            }
          };
          readerForDocx.onerror = reject;
          readerForDocx.readAsArrayBuffer(file);
        });
      } else {
        reject(new Error("Unsupported file type: " + file.type));
      }
    });
  };

  const formData = new FormData();

  const handleReplay = () => {
    if (videoRef.current) {
      videoRef.current.currentTime = 0; // Rewind the video to the beginning
      videoRef.current.play(); // Play the video
    }
  };
  // Initialize speech and question bank

  const handleNextQuestion = () => {
    // console.log("hai");
    callquestion("", answer)
      .then(() => {
        setVideoname(`/result_voice.mp4?timestamp=${Date.now()}`); // Forces React to detect a change
        if (videoRef.current) {
          videoRef.current.load(); // Reload the video
          videoRef.current.play(); // Ensure autoplay works
        }
      })
      .catch((err) => console.error("Error:", err));
  };

  const callquestion = (resume, answer) => {
    // console.log(resume)
    // console.log(answer)
    const apiUrl = "http://localhost:5000/run-function";
    return axios
      .get(apiUrl,{params:{param1:resume,param2:answer}})
      .then((response) => {
        setVideoname("/result_voice.mp4");
        // console.log(response.data);
        // console.log(response.data.result);
        // console.log(response.data.result[0]);
        setIsInterviewStarted(true);
        setQuestionget(response.data);
        console.log(resume,"\n",answer)
      })
      .catch((error) => {
        console.error("Error fetching data:", error);
      });
  };

  //   const callquestion = async (payload, withFile = false) => {
  //   try {
  //     let response;

  //     if (withFile) {
  //       // --- FormData when sending files ---
  //       const formData = new FormData();
  //       formData.append("answers", JSON.stringify(payload.answers));
  //       formData.append("resume", payload.resume);

  //       response = await axios.post("http://localhost:5000/run-function", formData, {
  //         headers: { "Content-Type": "multipart/form-data" },
  //       });
  //     } else {
  //       // --- JSON when sending strings only ---
  //       response = await axios.post("http://localhost:5000/run-function", payload, {
  //         headers: { "Content-Type": "application/json" },
  //       });
  //     }

  //     console.log(response.data);
  //     setVideoname("/result_voice.mp4");
  //     setIsInterviewStarted(true);
  //     setQuestionget(response.data);
  //   } catch (error) {
  //     console.error("Error fetching data:", error);
  //   }
  // };

  useEffect(() => {
    const { synth, recognition } = initializeSpeech();
    synthRef.current = synth;
    recognitionRef.current = recognition;

    if (recognition) {
      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setAnswer((prev) => prev + " " + transcript);
        setIsListening(false);
      };

      recognition.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };
    } else {
      console.warn("Speech recognition is not supported in this browser.");
    }

    // Default to behavioral questions
    setQuestionBank(getBehavioralQuestions());
  }, []);

  // Speak question when it changes
  // useEffect(() => {
  //   if (isInterviewStarted && questionBank.length > 0) {
  //     speakQuestion(synthRef.current, questionBank[questionIndex]);
  //   }
  // }, [questionIndex, isInterviewStarted, questionBank]);

  // Generate AI response
  // useEffect(() => {
  //   if (answer) {
  //     setAiResponse("");
  //     setTimeout(() => {
  //       const responses = [...getEncouragingResponses(), ...getFollowUpResponses()];
  //       setAiResponse(responses[Math.floor(Math.random() * responses.length)]);
  //     }, 1500);
  //   }
  // }, [answer]);

  // ========== Question Navigation ==========
  // const handleNextQuestion = () => {
  //   if (questionIndex < questionBank.length - 1) {
  //     setQuestionIndex((prev) => prev + 1);
  //     setAnswer("");                                                                         //handleNextQuestion
  //     // setAiResponse("");
  //   } else {
  //     synthRef.current.cancel();
  //     alert("AI Interview Completed! Redirecting...");
  //     navigate("/");
  //   }
  // };

  const handlePreviousQuestion = () => {
    if (questionIndex > 0) {
      setQuestionIndex((prev) => prev - 1);
      setAnswer("");
      // setAiResponse("");
    }
  };

  // ========== Question Bank Selection ==========
  const selectQuestionBank = (type) => {
    switch (type) {
      case "technical":
        setQuestionBank(getTechnicalQuestions());
        break;
      case "situational":
        setQuestionBank(getSituationalQuestions());
        break;
      default:
        setQuestionBank(getBehavioralQuestions());
    }
    setQuestionIndex(0);
    setAnswer("");
    // setAiResponse("");
  };

  // ========== Voice Control ==========
  const toggleVoiceInput = () => {
    if (!recognitionRef.current) {
      alert("Voice input is not supported in your browser");
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
    } else {
      recognitionRef.current.start();
    }
    setIsListening(!isListening);
  };

  // const replayQuestion = () => {
  //   speakQuestion(synthRef.current, questionBank[questionIndex]);
  // };

  return (
    <>
      <Background />
      <ContentWrapper>
        <Container maxWidth="sm">
          <Card
            sx={{
              p: 4,
              borderRadius: 3,
              boxShadow: 3,
              textAlign: "center",
              backgroundColor: "rgba(255, 255, 255, 0.1)",
              backdropFilter: "blur(10px)",
              color: "white",
            }}
          >
            {!isInterviewStarted ? (
              <>
                <Box sx={{ mb: 3 }}>
                  <img
                    src="ai.jpg"
                    alt="AI Interview"
                    style={{
                      width: "100%",
                      borderRadius: "10px",
                      maxHeight: "200px",
                      objectFit: "cover",
                    }}
                  />
                </Box>

                <Typography variant="h5" sx={{ mb: 3 }}>
                  Select Question Type
                </Typography>

                <Box
                  sx={{
                    display: "flex",
                    flexDirection: "column",
                    gap: 2,
                    mb: 3,
                  }}
                >
                  <Button
                    variant="outlined"
                    onClick={() => selectQuestionBank("behavioral")}
                    sx={{ color: "white", borderColor: "white" }}
                  >
                    Behavioral Questions
                  </Button>
                  <Button
                    variant="outlined"
                    onClick={() => selectQuestionBank("technical")}
                    sx={{ color: "white", borderColor: "white" }}
                  >
                    Technical Questions
                  </Button>
                  <Button
                    variant="outlined"
                    onClick={() => selectQuestionBank("situational")}
                    sx={{ color: "white", borderColor: "white" }}
                  >
                    Situational Questions
                  </Button>
                </Box>

                <Button
                  variant="contained"
                  onClick={async () => {
                    callquestion(resume, state.answers[0]);
                  }}
                  sx={{
                    backgroundColor: "#00c6ff",
                    "&:hover": { backgroundColor: "#0072ff" },
                    fontSize: "1.1rem",
                    padding: "10px 24px",
                  }}
                >
                  Start Interview
                </Button>
              </>
            ) : (
              <>
                <Box sx={{ textAlign: "center", mb: 2 }}>
                  <video
                    ref={videoRef}
                    width="100%"
                    height="auto"
                    autoPlay
                    style={{ borderRadius: "10px", maxHeight: "200px" }}
                  >
                    <source src={videoname} type="video/mp4" />
                  </video>
                  <Typography variant="h6" sx={{ mt: 1, fontWeight: "bold" }}>
                    AI Interviewer
                  </Typography>
                </Box>

                <Box
                  sx={{ display: "flex", alignItems: "center", gap: 1, mb: 2 }}
                >
                  <Typography variant="h5" sx={{ fontWeight: "bold" }}>
                    AI: {questionget.result}
                  </Typography>
                  <Button
                    variant="outlined"
                    onClick={handleReplay}
                    sx={{
                      color: "#00c6ff",
                      borderColor: "#00c6ff",
                      "&:hover": { backgroundColor: "#00c6ff20" },
                    }}
                  >
                    Replay
                  </Button>
                </Box>

                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  placeholder="Your response..."
                  sx={{
                    mb: 2,
                    input: { color: "white" },
                    "& .MuiOutlinedInput-root": {
                      "& fieldset": { borderColor: "white" },
                      "&:hover fieldset": { borderColor: "#66a3ff" },
                    },
                  }}
                />

                <Button
                  variant="contained"
                  onClick={toggleVoiceInput}
                  sx={{
                    mb: 2,
                    backgroundColor: isListening ? "#ff3b2f" : "#ff6f61",
                    "&:hover": {
                      backgroundColor: isListening ? "#ff2b1f" : "#ff5f51",
                    },
                  }}
                >
                  {isListening ? "Stop Recording" : "Start Voice Input"}
                </Button>

                {aiResponse && (
                  <Typography
                    variant="body1"
                    sx={{ mb: 2, fontWeight: "bold", color: "lightgreen" }}
                  >
                    AI: {questionget.result}
                  </Typography>
                )}

                <Box
                  sx={{
                    display: "flex",
                    justifyContent: "space-between",
                    mt: 2,
                  }}
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
                    {questionIndex < questionBank.length - 1
                      ? "Next Question"
                      : "Finish"}
                  </Button>
                </Box>
              </>
            )}
          </Card>
        </Container>
      </ContentWrapper>
    </>
  );
};

export default Interface;
