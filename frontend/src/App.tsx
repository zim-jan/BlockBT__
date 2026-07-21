import {BrowserRouter, Route, Routes} from 'react-router-dom'
import './assets/App.css'
import {BuilderPage} from './pages/BuilderPage'
import {LoginPage} from './pages/LoginPage'
import {SettingsPage} from './pages/SettingsPage'
import {ProtectedRoute} from './components/ProtectedRoute'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<BuilderPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
