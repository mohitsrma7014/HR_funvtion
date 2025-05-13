// src/components/SummaryCards.jsx
import React from 'react'
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Avatar,
  useTheme,
} from '@mui/material'
import {
  People as PeopleIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Event as EventIcon,
  AccessTime as AccessTimeIcon,
  Schedule as ScheduleIcon,
  Work as WorkIcon,
} from '@mui/icons-material'

const iconStyle = { fontSize: 40, opacity: 0.8 }

const SummaryCards = ({ data }) => {
  const theme = useTheme()

  const cards = [
    {
      title: 'Total Employees',
      value: data.totalEmployees,
      icon: <PeopleIcon sx={iconStyle} />,
      color: theme.palette.primary.main,
    },
    {
      title: 'Present Days',
      value: data.totalPresent,
      icon: <CheckCircleIcon sx={iconStyle} />,
      color: theme.palette.success.main,
    },
    {
      title: 'Absent Days',
      value: data.totalAbsent,
      icon: <CancelIcon sx={iconStyle} />,
      color: theme.palette.error.main,
    },
    {
      title: 'Holidays',
      value: data.totalHolidays,
      icon: <EventIcon sx={iconStyle} />,
      color: theme.palette.warning.main,
    },
    {
      title: 'On Duty',
      value: data.totalOD,
      icon: <WorkIcon sx={iconStyle} />,
      color: theme.palette.info.main,
    },
    {
      title: 'Total Work Hours',
      value: data.totalWorkingHours.toFixed(2),
      icon: <AccessTimeIcon sx={iconStyle} />,
      color: theme.palette.secondary.main,
    },
    {
      title: 'Total OT Hours',
      value: data.totalOvertime.toFixed(2),
      icon: <ScheduleIcon sx={iconStyle} />,
      color: theme.palette.success.dark,
    },
  ]

  return (
    <Grid container spacing={3} sx={{ mb: 3 }}>
      {cards.map((card, index) => (
        <Grid item xs={12} sm={6} md={4} lg={3} key={index}>
          <Card sx={{ height: '100%' }}>
            <CardContent>
              <Box
                sx={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div>
                  <Typography
                    variant="subtitle2"
                    color="text.secondary"
                    gutterBottom
                  >
                    {card.title}
                  </Typography>
                  <Typography variant="h4" component="div">
                    {card.value}
                  </Typography>
                </div>
                <Avatar
                  sx={{
                    backgroundColor: `${card.color}20`,
                    color: card.color,
                    width: 60,
                    height: 60,
                  }}
                >
                  {card.icon}
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  )
}

export default SummaryCards