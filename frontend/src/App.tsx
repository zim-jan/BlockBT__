import {BrowserRouter, Route, Routes} from 'react-router-dom'
import './assets/App.css'
import {BuilderPage} from './pages/BuilderPage'
import {LoginPage} from './pages/LoginPage'
import {SettingsPage} from './pages/SettingsPage'
import {DashboardPage} from './pages/DashboardPage'
import {ProtectedRoute} from './components/ProtectedRoute'
import {ToastContainer} from './components/ui/ToastContainer'

function App() {
  return (
    <BrowserRouter>
      <ToastContainer />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<BuilderPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
