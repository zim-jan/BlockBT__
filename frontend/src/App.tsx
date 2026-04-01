import {BrowserRouter, Route, Routes} from 'react-router-dom'
import './assets/App.css'
import {BuilderPage} from './pages/BuilderPage'
import {SettingsPage} from './pages/SettingsPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<BuilderPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
