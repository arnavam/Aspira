import React from 'react';
import {
  Box,
  Typography,
  Container,
  Grid,
  Card,
  CardContent,
  Avatar,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Tabs,
  Tab,
  Divider,
  Button
} from '@mui/material';
import { 
  TrendingUp,
  Business,
  LocationOn,
  Work,
  EmojiEvents,
  Person
} from '@mui/icons-material';

const Dashboard = () => {
  const [tabValue, setTabValue] = React.useState(0);

  // Mock data - replace with real data
  const userRank = {
    position: 15,
    totalUsers: 1000,
    score: 92.5,
    progress: 65,
    recentCompanies: ['Google', 'Microsoft', 'Amazon']
  };

  const leaderboard = [
    { id: 1, name: 'Ajay krishna', score: 98.7, country: 'USA' },
    { id: 2, name: 'benson', score: 97.9, country: 'India' },
    { id: 3, name: 'Sree hari', score: 97.5, country: 'UK' },
    // ... more entries
  ];

  const leadingCompanies = [
    { name: 'Google', openings: 234, hiringScore: 9.8 },
    { name: 'Microsoft', openings: 189, hiringScore: 9.5 },
    { name: 'Amazon', openings: 302, hiringScore: 9.2 },
    // ... more companies
  ];

  const vacancies = {
    'USA': [
      { title: 'Senior Software Engineer', company: 'Google', location: 'Mountain View, CA' },
      { title: 'Data Scientist', company: 'Microsoft', location: 'Redmond, WA' }
    ],
    'India': [
      { title: 'Full Stack Developer', company: 'Flipkart', location: 'Bangalore' },
      { title: 'Cloud Architect', company: 'TCS', location: 'Mumbai' }
    ],
    'Germany': [
      { title: 'AI Researcher', company: 'SAP', location: 'Berlin' },
      { title: 'DevOps Engineer', company: 'BMW', location: 'Munich' }
    ]
  };

  return (
    <>
      {/* Full-Screen Background */}
      <Box
        sx={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          backgroundImage: `url('bg.jpg')`,
          backgroundSize: 'cover', // Ensures the image covers the entire screen
          backgroundPosition: 'center', // Centers the image
          backgroundRepeat: 'no-repeat', // Prevents the image from repeating
          zIndex: -1, // Ensures the background stays behind the content
        }}
      />

      {/* Content */}
      <Container 
        maxWidth="xl" 
        sx={{ 
          py: 4,
          position: 'relative', // Ensures content is above the background
          zIndex: 1, // Ensures content is above the background
          minHeight: '100vh', // Ensures the container takes up at least the full viewport height
          width: '100%', // Ensures the container takes up the full width
        }}
      >
        <Typography variant="h4" gutterBottom sx={{ fontWeight: 'bold', mb: 4, color: 'white' }}>
          <EmojiEvents sx={{ mr: 1, verticalAlign: 'bottom' }} />
          Career Dashboard
        </Typography>

        <Grid container spacing={4}>
          {/* User Ranking Section */}
          <Grid item xs={12} md={4}>
            <Card sx={{ height: '100%', boxShadow: 3 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                    <Person />
                  </Avatar>
                  <Typography variant="h6">Your Ranking</Typography>
                </Box>

                <Box sx={{ textAlign: 'center', mb: 3 }}>
                  <Chip 
                    label={`Rank ${userRank.position} / ${userRank.totalUsers}`}
                    color="primary"
                    sx={{ fontSize: '1.2rem', p: 2 }}
                  />
                  <Typography variant="h3" sx={{ my: 2 }}>
                    {userRank.score}
                  </Typography>
                  <Typography color="text.secondary">
                    Performance Score
                  </Typography>
                </Box>

                <Divider sx={{ my: 2 }} />

                <Typography variant="subtitle1" gutterBottom>
                  Recent Company Opportunities
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  {userRank.recentCompanies.map(company => (
                    <Chip
                      key={company}
                      label={company}
                      icon={<Business fontSize="small" />}
                      variant="outlined"
                    />
                  ))}
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Global Leaderboard */}
          <Grid item xs={12} md={8}>
            <Card sx={{ boxShadow: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <TrendingUp sx={{ mr: 1, verticalAlign: 'bottom' }} />
                  Global Leaderboard
                </Typography>
                
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Rank</TableCell>
                        <TableCell>Name</TableCell>
                        <TableCell align="right">Score</TableCell>
                        <TableCell>Country</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {leaderboard.map((user, index) => (
                        <TableRow key={user.id}>
                          <TableCell>#{index + 1}</TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                              <Avatar sx={{ width: 24, height: 24, mr: 1 }} />
                              {user.name}
                            </Box>
                          </TableCell>
                          <TableCell align="right">{user.score}</TableCell>
                          <TableCell>
                            <Chip 
                              label={user.country} 
                              size="small" 
                              icon={<LocationOn fontSize="small" />}
                            />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>

          {/* Leading Companies */}
          <Grid item xs={12}>
            <Card sx={{ boxShadow: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <Business sx={{ mr: 1, verticalAlign: 'bottom' }} />
                  Top Hiring Companies
                </Typography>
                
                <Grid container spacing={3}>
                  {leadingCompanies.map(company => (
                    <Grid item xs={12} sm={6} md={4} key={company.name}>
                      <Paper sx={{ p: 2 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                          <Avatar sx={{ bgcolor: 'secondary.main', mr: 2 }}>
                            {company.name[0]}
                          </Avatar>
                          <Typography variant="h6">{company.name}</Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                          <div>
                            <Typography variant="body2">Open Positions</Typography>
                            <Typography variant="h6">{company.openings}</Typography>
                          </div>
                          <div>
                            <Typography variant="body2">Hiring Score</Typography>
                            <Typography variant="h6">{company.hiringScore}/10</Typography>
                          </div>
                        </Box>
                      </Paper>
                    </Grid>
                  ))}
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          {/* Job Vacancies by Country */}
          <Grid item xs={12}>
            <Card sx={{ boxShadow: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  <Work sx={{ mr: 1, verticalAlign: 'bottom' }} />
                  Current Job Vacancies
                </Typography>
                
                <Tabs 
                  value={tabValue} 
                  onChange={(e, newValue) => setTabValue(newValue)}
                  sx={{ mb: 3 }}
                >
                  {Object.keys(vacancies).map(country => (
                    <Tab key={country} label={country} />
                  ))}
                </Tabs>

                {Object.entries(vacancies).map(([country, jobs], index) => (
                  tabValue === index && (
                    <Grid container spacing={2} key={country}>
                      {jobs.map((job, jobIndex) => (
                        <Grid item xs={12} md={6} key={jobIndex}>
                          <Paper sx={{ p: 2 }}>
                            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                              <div>
                                <Typography variant="subtitle1">{job.title}</Typography>
                                <Typography variant="body2" color="text.secondary">
                                  {job.company} • {job.location}
                                </Typography>
                              </div>
                              <Button 
                                variant="contained" 
                                size="small"
                                startIcon={<LocationOn />}
                              >
                                Apply
                              </Button>
                            </Box>
                          </Paper>
                        </Grid>
                      ))}
                    </Grid>
                  )
                ))}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Container>
    </>
  );
};

export default Dashboard;