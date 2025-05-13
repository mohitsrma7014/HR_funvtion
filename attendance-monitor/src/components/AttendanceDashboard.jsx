// src/components/AttendanceDashboard.jsx
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'
import { format, startOfMonth, endOfMonth, parseISO } from 'date-fns'
import {
  Box,
  Typography,
  Paper,
  Grid,
  CircularProgress,
  Alert,
  Button,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
} from '@mui/material'
import { DataGrid } from '@mui/x-data-grid'
import {
  Summarize as SummarizeIcon,
  CalendarMonth as CalendarMonthIcon,
  FilterAlt as FilterAltIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material'
import SummaryCards from './SummaryCards'
import AttendanceChart from './AttendanceChart'

const currentDate = new Date()
const currentMonth = currentDate.getMonth() + 1
const currentYear = currentDate.getFullYear()

const fetchAttendanceData = async (month, year) => {
  const response = await axios.post(
    'http://127.0.0.1:8000/api/api/attendance/process/',
    { month, year }
  )
  return response.data
}

const AttendanceDashboard = () => {
  const [month, setMonth] = useState(currentMonth)
  const [year, setYear] = useState(currentYear)

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ['attendance', month, year],
    queryFn: () => fetchAttendanceData(month, year),
    keepPreviousData: true,
    staleTime: 1000 * 60 * 5, // 5 minutes
  })

  const handleMonthChange = (event) => {
    setMonth(event.target.value)
  }

  const handleYearChange = (event) => {
    setYear(event.target.value)
  }

  const handleRefresh = () => {
    refetch()
  }

  // Process data for summary cards
  const summaryData = data?.reduce(
    (acc, employee) => {
      acc.totalEmployees += 1
      acc.totalPresent += employee.total_present_days
      acc.totalAbsent += employee.total_absent_days
      acc.totalHolidays += employee.total_holiday_days
      acc.totalOD += employee.total_od_days
      acc.totalWorkingHours += parseFloat(employee.total_working_hours)
      acc.totalOvertime += parseFloat(employee.total_overtime_hours)
      return acc
    },
    {
      totalEmployees: 0,
      totalPresent: 0,
      totalAbsent: 0,
      totalHolidays: 0,
      totalOD: 0,
      totalWorkingHours: 0,
      totalOvertime: 0,
    }
  )

  // Process data for the chart
  const chartData = data?.map((employee) => ({
    name: employee.employee_name,
    present: employee.total_present_days,
    absent: employee.total_absent_days,
    od: employee.total_od_days,
  }))

  // Columns for the data grid
  const columns = [
    { field: 'employee_id', headerName: 'ID', width: 80 },
    { field: 'employee_name', headerName: 'Name', width: 180 },
    { field: 'department', headerName: 'Department', width: 150 },
    {
      field: 'total_present_days',
      headerName: 'Present',
      width: 100,
      type: 'number',
    },
    {
      field: 'total_absent_days',
      headerName: 'Absent',
      width: 100,
      type: 'number',
    },
    {
      field: 'total_od_days',
      headerName: 'OD Days',
      width: 100,
      type: 'number',
    },
    {
      field: 'total_working_hours',
      headerName: 'Work Hours',
      width: 120,
      type: 'number',
      valueFormatter: (params) => `${params.value.toFixed(2)} hrs`,
    },
    {
      field: 'total_overtime_hours',
      headerName: 'OT Hours',
      width: 120,
      type: 'number',
      valueFormatter: (params) => `${params.value.toFixed(2)} hrs`,
    },
    {
      field: 'actions',
      headerName: 'Details',
      width: 120,
      renderCell: (params) => (
        <Button
          variant="outlined"
          size="small"
          onClick={() => handleViewDetails(params.row)}
        >
          View
        </Button>
      ),
    },
  ]

  const handleViewDetails = (employee) => {
    // Implement modal or navigation to detailed view
    console.log('View details for:', employee.employee_name)
  }

  return (
    <Box sx={{ p: 3 }}>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={3} alignItems="center">
          <Grid item xs={12} md={6}>
            <Typography variant="h4" component="h1" gutterBottom>
              <SummarizeIcon sx={{ verticalAlign: 'middle', mr: 1 }} />
              Attendance Monitoring System
            </Typography>
            <Typography variant="subtitle1" color="text.secondary">
              {format(startOfMonth(new Date(year, month - 1)), 'MMMM yyyy')} Report
            </Typography>
          </Grid>
          <Grid item xs={12} md={6}>
            <Box
              sx={{
                display: 'flex',
                gap: 2,
                justifyContent: 'flex-end',
                flexWrap: 'wrap',
              }}
            >
              <FormControl size="small" sx={{ minWidth: 120 }}>
                <InputLabel id="month-select-label">Month</InputLabel>
                <Select
                  labelId="month-select-label"
                  id="month-select"
                  value={month}
                  label="Month"
                  onChange={handleMonthChange}
                >
                  {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                    <MenuItem key={m} value={m}>
                      {format(new Date(2000, m - 1, 1), 'MMMM')}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <FormControl size="small" sx={{ minWidth: 120 }}>
                <InputLabel id="year-select-label">Year</InputLabel>
                <Select
                  labelId="year-select-label"
                  id="year-select"
                  value={year}
                  label="Year"
                  onChange={handleYearChange}
                >
                  {Array.from({ length: 5 }, (_, i) => currentYear - 2 + i).map(
                    (y) => (
                      <MenuItem key={y} value={y}>
                        {y}
                      </MenuItem>
                    )
                  )}
                </Select>
              </FormControl>
              <Button
                variant="contained"
                startIcon={<FilterAltIcon />}
                onClick={() => refetch()}
              >
                Apply
              </Button>
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={handleRefresh}
              >
                Refresh
              </Button>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {isError && (
        <Alert severity="error" sx={{ mb: 3 }}>
          Error loading attendance data: {error.message}
        </Alert>
      )}

      {data && (
        <>
          <SummaryCards data={summaryData} />
          <AttendanceChart data={chartData} />
          
          <Paper sx={{ p: 2, mt: 3 }}>
            <Typography variant="h6" gutterBottom>
              Employee Attendance Summary
            </Typography>
            <Box sx={{ height: 600, width: '100%' }}>
              <DataGrid
                rows={data}
                columns={columns}
                pageSize={10}
                rowsPerPageOptions={[10, 25, 50]}
                disableSelectionOnClick
                loading={isLoading}
                getRowId={(row) => row.employee_id}
                sx={{
                  '& .MuiDataGrid-cell:focus': {
                    outline: 'none',
                  },
                }}
              />
            </Box>
          </Paper>
        </>
      )}
    </Box>
  )
}

export default AttendanceDashboard