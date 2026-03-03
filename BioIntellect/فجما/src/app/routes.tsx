import { createBrowserRouter } from "react-router";
import DoctorDashboard from "./pages/DoctorDashboard";
import PatientDashboard from "./pages/PatientDashboard";
import MRIAnalysis from "./pages/MRIAnalysis";
import ECGAnalysis from "./pages/ECGAnalysis";
import NotFound from "./pages/NotFound";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: DoctorDashboard,
  },
  {
    path: "/doctor",
    Component: DoctorDashboard,
  },
  {
    path: "/patient",
    Component: PatientDashboard,
  },
  {
    path: "/mri-analysis/:patientId?",
    Component: MRIAnalysis,
  },
  {
    path: "/ecg-analysis/:patientId?",
    Component: ECGAnalysis,
  },
  {
    path: "*",
    Component: NotFound,
  },
]);
