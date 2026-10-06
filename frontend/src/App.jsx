import { Route, Routes } from "react-router-dom";
import Header from "./components/Header";
import Toast from "./components/Toast";
import MyPage from "./pages/MyPage";
import RoomsPage from "./pages/RoomsPage";
import StudyDetailPage from "./pages/StudyDetailPage";
import StudyListPage from "./pages/StudyListPage";

export default function App() {
  return (
    <>
      <Header />
      <main className="container">
        <Routes>
          <Route path="/" element={<StudyListPage />} />
          <Route path="/studies/:id" element={<StudyDetailPage />} />
          <Route path="/rooms" element={<RoomsPage />} />
          <Route path="/me" element={<MyPage />} />
          <Route path="*" element={<p className="muted">페이지를 찾을 수 없습니다.</p>} />
        </Routes>
      </main>
      <Toast />
    </>
  );
}
