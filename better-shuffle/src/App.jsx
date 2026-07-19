import { useState } from 'react'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import './App.css'
import { Routes, Route } from 'react-router'

function App() {

  return ( <div>
    <Routes>
      <Route path= '/' element={<Login />} />
      <Route path = '/Dashboard' element={<Dashboard />} />


    </Routes>
  </div> )
}

export default App
