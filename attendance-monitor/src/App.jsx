// src/App.jsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import AttendanceDashboard from './components/AttendanceDashboard'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'

const queryClient = new QueryClient()

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#90caf9',
    },
    secondary: {
      main: '#f48fb1',
    },
  },
})

function App() {
  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <QueryClientProvider client={queryClient}>
        <div className="app-container">
          <AttendanceDashboard />
        </div>
      </QueryClientProvider>
    </ThemeProvider>
  )
}

export default App