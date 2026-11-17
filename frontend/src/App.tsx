import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "@/components/layout/Layout";
import Libraries from "@/pages/Libraries";
import Library from "@/pages/Library";
import Tutor from "@/pages/Tutor";
import Vocabulary from "@/pages/Vocabulary";
import Speaking from "@/pages/Speaking";
import Progress from "@/pages/Progress";
import Health from "@/pages/Health";
import { JobsProvider } from "@/contexts/JobsContext";

export default function App() {
  return (
    <JobsProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Libraries />} />
            <Route path="books" element={<Library />} />
            <Route path="tutor" element={<Tutor />} />
            <Route path="vocabulary" element={<Vocabulary />} />
            <Route path="speaking" element={<Speaking />} />
            <Route path="progress" element={<Progress />} />
            <Route path="health" element={<Health />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </JobsProvider>
  );
}