import { Container, Grid, Card, Typography, Avatar, Box, Button } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import InterviewIcon from '@mui/icons-material/VideoCall';
import { styled } from "@mui/material/styles";

// 📌 Styled Components
const Background = styled(Box)({
  position: "fixed", // Fix the background to the viewport
  top: 0,
  left: 0,
  width: "100%",
  height: "100%",
  backgroundImage: `url('bg.jpg')`,
  backgroundSize: "cover",
  backgroundPosition: "center",
  backgroundRepeat: "no-repeat",
  zIndex: -1, // Ensure the background stays behind the content
  "&::before": {
    content: '""',
    position: "absolute",
    top: 0,
    left: 0,
    width: "100%",
    height: "100%",
    backgroundColor: "rgba(0, 0, 0, 0.5)", // Dark overlay
    zIndex: 1,
  },
});

const ContentWrapper = styled(Box)({
  position: "relative",
  zIndex: 2, // Ensure content is above the background
  minHeight: "100vh",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  padding: "20px",
});

const Home = () => {
  const navigate = useNavigate();
  const username = localStorage.getItem('username') || 'Guest';
  const isGuest = username === 'Guest';

  const handleMockInterview = () => {
    navigate('/mock-interview');
  };

  return (
    <>
      <Background />
      <ContentWrapper>
        <Container sx={{ mt: 10, padding: 3 }}>
          {/* Welcome Message */}
          <Typography variant="h3" gutterBottom sx={{ mb: 4, color: "white", fontWeight: "bold" }}>
            Welcome {username}!
          </Typography>

          <Grid container spacing={3} justifyContent="center"> {/* Center the grid content */}
            {/* User Profile Card */}
            <Grid item xs={12} md={4}>
              <Card sx={{ p: 3, height: '100%', backgroundColor: "rgba(255, 255, 255, 0.1)", backdropFilter: "blur(10px)" }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Avatar sx={{ 
                    width: 56, 
                    height: 56, 
                    bgcolor: 'primary.main',
                    fontSize: '1.5rem'
                  }}>
                    {username[0].toUpperCase()}
                  </Avatar>
                  <Box>
                    <Typography variant="h6" sx={{ color: "white", fontWeight: "bold" }}>{username}</Typography>
                    <Typography variant="body2" sx={{ color: "rgba(255, 255, 255, 0.7)" }}>
                      {isGuest ? 'Guest User' : 'Registered User'}
                    </Typography>
                  </Box>
                </Box>
              </Card>
            </Grid>

            {/* Rank Card */}
            <Grid item xs={12} md={4}>
              <Card sx={{ p: 3, height: '100%', textAlign: 'center', backgroundColor: "rgba(255, 255, 255, 0.1)", backdropFilter: "blur(10px)" }}>
                <Typography variant="h6" gutterBottom sx={{ color: "white", fontWeight: "bold" }}>
                  Current Rank
                </Typography>
                <Typography variant="h2" sx={{ color: "primary.main", fontWeight: "bold" }}>
                  #15
                </Typography>
                <Typography variant="body2" sx={{ color: "rgba(255, 255, 255, 0.7)" }}>
                  Top 10% of Users
                </Typography>
              </Card>
            </Grid>

            {/* Progress Card */}
            <Grid item xs={12} md={4}>
              <Card sx={{ p: 3, height: '100%', textAlign: 'center', backgroundColor: "rgba(255, 255, 255, 0.1)", backdropFilter: "blur(10px)" }}>
                <Typography variant="h6" gutterBottom sx={{ color: "white", fontWeight: "bold" }}>
                  Interview Progress
                </Typography>
                <Box sx={{ 
                  width: 100,
                  height: 100,
                  margin: 'auto',
                  borderRadius: '50%',
                  backgroundColor: 'primary.light',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <Typography variant="h5" sx={{ color: "white", fontWeight: "bold" }}>75%</Typography>
                </Box>
              </Card>
            </Grid>

            {/* Mock Interview Card */}
            <Grid item xs={12} md={6} display="flex" justifyContent="center"> {/* Center the card */}
              <Card 
                sx={{ 
                  p: 3, 
                  width: '100%', // Ensure the card takes full width of the grid item
                  maxWidth: 500, // Optional: Set a max width for better appearance
                  cursor: 'pointer', 
                  transition: 'transform 0.3s',
                  backgroundColor: "rgba(255, 255, 255, 0.1)",
                  backdropFilter: "blur(10px)",
                  '&:hover': {
                    transform: 'scale(1.02)',
                    boxShadow: 3
                  }
                }}
                onClick={handleMockInterview}
              >
                <Box sx={{ 
                  display: 'flex', 
                  flexDirection: 'column', 
                  alignItems: 'center', 
                  justifyContent: 'center',
                  height: '100%',
                  textAlign: 'center' // Center-align text
                }}>
                  <InterviewIcon sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
                  <Typography variant="h5" gutterBottom sx={{ color: "white", fontWeight: "bold" }}>
                    Start Mock Interview
                  </Typography>
                  <Typography variant="body2" sx={{ color: "rgba(255, 255, 255, 0.7)", mb: 2 }}>
                    Practice with AI-powered interviews
                  </Typography>
                  <Button 
                    variant="contained" 
                    sx={{ mt: 2 }}
                    startIcon={<InterviewIcon />}
                  >
                    Begin Now
                  </Button>
                </Box>
              </Card>
            </Grid>
          </Grid>
        </Container>
      </ContentWrapper>
    </>
  );
};

export default Home;