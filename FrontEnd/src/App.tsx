import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import Login from './pages/Login';
import DocumentUpload from './pages/DocumentUpload';
import DocumentResults from './pages/DocumentResults';
import DocumentHistory from './pages/DocumentHistory';
import EventsHistory from './pages/EventsHistory';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';

import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/upload" replace />} />
            <Route path="upload" element={<DocumentUpload />} />
            <Route path="results" element={<DocumentResults />} />
            <Route path="history" element={<DocumentHistory />} />
            <Route path="events" element={<EventsHistory />} />
          </Route>
        </Routes>
        <ToastContainer
          position="top-right"
          autoClose={5000}
          hideProgressBar={false}
          newestOnTop={false}
          closeOnClick
          rtl={false}
          pauseOnFocusLoss
          draggable
          pauseOnHover
        />
      </div>
    </Router>
  );
}

export default App;

