import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "@/components/layout/Layout";
import Library from "@/pages/Library";
import Tutor from "@/pages/Tutor";
import Vocabulary from "@/pages/Vocabulary";
import Progress from "@/pages/Progress";
import Speaking from "@/pages/Speaking";
import Health from "@/pages/Health";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Library />} />
          <Route path="tutor" element={<Tutor />} />
          <Route path="vocabulary" element={<Vocabulary />} />
          <Route path="speaking" element={<Speaking />} />
          <Route path="progress" element={<Progress />} />
          <Route path="health" element={<Health />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}