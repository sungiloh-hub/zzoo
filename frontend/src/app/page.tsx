"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Flame, Loader2, Utensils, Soup, Salad, Coffee, MapPin } from "lucide-react";

const COURSE_ICONS: Record<string, any> = {
  "윈디쉬": Coffee,
  "진국": Soup,
  "면가": Utensils,
  "샐러데이": Salad
};

export default function Home() {
  const [targetCalories, setTargetCalories] = useState<string>("2000");
  const [selectedCourse, setSelectedCourse] = useState<string | null>(null);
  const [courses, setCourses] = useState<any[]>([]);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [loadingMenus, setLoadingMenus] = useState(true);
  const [loadingRecs, setLoadingRecs] = useState(false);
  const [remainingCals, setRemainingCals] = useState<number>(0);
  const [coords, setCoords] = useState<{lat: number, lon: number} | null>(null);

  const today = new Date().toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

  useEffect(() => {
    // 1. Fetch Today's Menu
    fetch(`${API_BASE_URL}/api/menu/today`)
      .then(res => res.json())
      .then(data => {
        const fetchedMenus = data.menus;
        const menuArray = [
          { id: "윈디쉬", title: "윈디쉬", ...fetchedMenus["윈디쉬"] },
          { id: "진국", title: "진국", ...fetchedMenus["진국"] },
          { id: "면가", title: "면가", ...fetchedMenus["면가"] },
          { id: "샐러데이", title: "샐러데이", ...fetchedMenus["샐러데이"] }
        ];
        setCourses(menuArray);
        setLoadingMenus(false);
      })
      .catch((e) => {
        console.error("Backend offline or error", e);
        setLoadingMenus(false);
      });
    // 2. Get User Location
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        (pos) => setCoords({ lat: pos.coords.latitude, lon: pos.coords.longitude }),
        (err) => console.log("위치 정보 활용 불가:", err.message),
        { enableHighAccuracy: true, timeout: 5000, maximumAge: 0 }
      );
    }
  }, []);

  const handleSelectCourse = async (courseId: string) => {
    setSelectedCourse(courseId);
    setLoadingRecs(true);
    setRecommendations([]);

    try {
      const res = await fetch(`${API_BASE_URL}/api/recommend`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target_calories: parseInt(targetCalories) || 2000,
          selected_course: courseId,
          latitude: coords?.lat || 0,
          longitude: coords?.lon || 0
        })
      });
      
      if (!res.ok) {
        const errorData = await res.json();
        alert(`🚨 AI 추천을 불러올 수 없습니다.\n오류 원인: ${errorData.detail || "서버 통신 에러"}`);
        setLoadingRecs(false);
        return;
      }

      const data = await res.json();
      setRecommendations(data.recommendations || []);
      setRemainingCals(data.remaining_calories);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingRecs(false);
    }
  };

  const selectedData = courses.find((c) => c.id === selectedCourse);
  const displayRemainingCals = remainingCals !== 0 ? remainingCals : (parseInt(targetCalories || "2000") - (selectedData?.calories || 0));

  return (
    <div className="min-h-screen flex justify-center text-slate-800 font-sans bg-slate-900 relative overflow-hidden">
      {/* Modern Mesh Gradient Ambient Background */}
      <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-indigo-500 rounded-full mix-blend-screen filter blur-[120px] opacity-40" />
      <div className="absolute top-[20%] right-[-10%] w-[60%] h-[60%] bg-rose-500 rounded-full mix-blend-screen filter blur-[130px] opacity-30" />
      <div className="absolute bottom-[-10%] left-[20%] w-[50%] h-[50%] bg-amber-500 rounded-full mix-blend-screen filter blur-[100px] opacity-20" />

      <main className="w-full max-w-md bg-white/95 backdrop-blur-2xl min-h-screen z-10 shadow-[0_0_80px_rgba(0,0,0,0.5)] overflow-y-auto relative no-scrollbar">
        {/* Header Section */}
        <div className="pt-16 pb-6 px-8 flex flex-col items-center">
          <p className="text-sm font-semibold text-slate-400 mb-2 tracking-widest uppercase">{today}</p>
          <div className="flex flex-col items-center space-y-1 mt-6">
            <span className="text-xs text-slate-400 font-semibold tracking-wider">나의 목표 칼로리</span>
            <div className="flex items-baseline space-x-1 border-b-2 border-transparent focus-within:border-slate-800 transition-colors px-4 pb-1">
              <input
                type="number"
                value={targetCalories}
                onChange={(e) => setTargetCalories(e.target.value)}
                className="text-5xl font-light text-center w-36 bg-transparent outline-none p-0 text-slate-900"
                placeholder="2000"
              />
              <span className="text-xl font-medium text-slate-300">kcal</span>
            </div>
          </div>
        </div>

        {/* Middle Section: Course Selection */}
        <div className="px-6 pb-6 mt-4">
          <h2 className="text-[17px] font-semibold text-slate-800 mb-4 px-2 tracking-tight">
            오늘 구내식당 코스를 선택해주세요!
          </h2>
          
          {loadingMenus ? (
            <div className="flex justify-center items-center py-10 opacity-50 text-sm">
               <Loader2 className="animate-spin w-4 h-4 mr-2" /> PDF 식단표 불러오는 중...
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-4">
              <AnimatePresence>
                {courses.map((course) => (
                  <motion.button
                    key={course.id}
                    onClick={() => handleSelectCourse(course.id)}
                    whileTap={{ scale: 0.96 }}
                    className={`relative p-5 rounded-[28px] flex flex-col items-start transition-all duration-300 ${
                      selectedCourse === course.id
                        ? "bg-slate-900 text-white shadow-xl shadow-slate-400/30"
                        : "bg-white text-slate-800 shadow-[0_4px_24px_rgba(0,0,0,0.03)] border border-slate-100"
                    }`}
                  >
                    {course.image_url ? (
                      <div className="w-14 h-14 rounded-full overflow-hidden mb-4 shadow-sm border-2 border-slate-50 flex-shrink-0">
                        <img
                          src={course.image_url}
                          alt={course.title}
                          className="w-full h-full object-cover"
                          loading="lazy"
                        />
                      </div>
                    ) : (() => {
                      const Icon = COURSE_ICONS[course.id] || Utensils;
                      return <Icon className={`w-8 h-8 mb-4 ${selectedCourse === course.id ? "text-slate-300" : "text-slate-500"}`} />;
                    })()}
                    <span className="text-[13px] font-bold truncate w-full text-left leading-tight">
                      {course.menu_name || "메뉴 미정"}
                    </span>
                    <span className={`text-[11px] mt-1 font-semibold flex items-center ${selectedCourse === course.id ? "text-slate-300" : "text-slate-400"}`}>
                       <Flame className="w-3 h-3 text-orange-400 mr-0.5" strokeWidth={3}/> {course.calories || 0} kcal
                    </span>
                  </motion.button>
                ))}
              </AnimatePresence>
            </div>
          )}
        </div>

        {/* Selected Course Bubble */}
        <AnimatePresence>
          {selectedCourse && selectedData && !loadingRecs && (
            <motion.div
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ delay: 0.2, type: "spring", stiffness: 300, damping: 25 }}
              className="mx-6 px-5 py-4 bg-slate-50 border border-slate-100 rounded-2xl flex items-center justify-between mt-2"
            >
              <div className="flex items-center space-x-3">
                <div className="flex flex-col">
                  <span className="text-[13px] font-bold text-slate-800">
                    {selectedData.menu_name}
                  </span>
                  <span className="text-[11px] font-medium text-slate-400">
                    실제 식단 조회됨
                  </span>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Bottom Section: Remaining Calories & Recommendations */}
        <AnimatePresence>
          {selectedCourse && (
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1, duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
              className="mt-8 bg-slate-900 w-full min-h-[400px] rounded-t-[40px] pt-8 pb-12 shadow-[0_-10px_40px_rgba(0,0,0,0.1)]"
            >
              <div className="px-8 mb-8 text-center text-white">
                <p className="text-xs font-bold tracking-widest text-slate-400 mb-2 uppercase">
                  Remaining Calories
                </p>
                <div className="flex items-center justify-center space-x-1">
                  <span className="text-6xl font-light tracking-tighter text-white flex items-center">
                    {displayRemainingCals} <span className="text-xl text-slate-500 font-medium ml-2">kcal</span>
                  </span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-1 mt-8 overflow-hidden">
                  <motion.div 
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.max(0, Math.min((displayRemainingCals / (parseInt(targetCalories) || 2000)) * 100, 100))}%` }}
                    transition={{ duration: 1, delay: 0.3, ease: "easeOut" }}
                    className="bg-green-400 h-full rounded-full"
                  />
                </div>
              </div>

              {loadingRecs ? (
                <div className="flex flex-col items-center justify-center py-10 text-slate-400">
                  <Loader2 className="animate-spin w-8 h-8 mb-4 opacity-50 text-white" />
                  <span className="text-sm">Agent가 저녁 메뉴를 추천하고 있습니다...</span>
                </div>
              ) : (
                <div className="px-6">
                  <div className="flex flex-col pb-8 pt-2 space-y-6">
                    {recommendations.map((rec, i) => (
                      <motion.div
                        key={i}
                        initial={{ opacity: 0, y: 30 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 + i * 0.1, duration: 0.5 }}
                        className="w-full bg-white rounded-[28px] overflow-hidden shadow-xl flex flex-col"
                      >
                        {/* Dynamic Generative AI Food Image */}
                        <div className="h-48 w-full relative bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center">
                          {rec.english_name ? (
                            <img 
                              src={`https://loremflickr.com/400/300/${encodeURIComponent(rec.english_name.replace(/ /g, '').toLowerCase())},food?lock=${Date.now() + i}`} 
                              alt={rec.menu_name}
                              className="object-cover w-full h-full"
                              loading="lazy"
                            />
                          ) : (
                            <span className="text-6xl">🍽️</span>
                          )}
                        </div>
                        
                        <div className="p-6">
                          <div className="flex justify-between items-start mb-4">
                            <span className="px-3 py-1 bg-slate-100 text-slate-700 text-[10px] font-bold rounded-full tracking-wide truncate max-w-[120px]">
                              {rec.reason || "추천 메뉴"}
                            </span>
                            <span className="text-lg font-black text-slate-900 tracking-tight flex-shrink-0">
                              {rec.calories}
                              <span className="text-[11px] font-bold text-slate-400 ml-1">kcal</span>
                            </span>
                          </div>
                          
                          <div className={`flex items-start justify-between ${rec.restaurant_name ? 'mb-3' : 'mb-6'} h-12 gap-2`}>
                            <h3 className="text-[17px] font-bold text-slate-800 leading-snug line-clamp-2">
                              {rec.menu_name}
                            </h3>
                            <a 
                              href={`https://map.naver.com/v5/search/${encodeURIComponent(rec.restaurant_name ? rec.restaurant_name : rec.menu_name)}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="flex items-center justify-center space-x-1 bg-indigo-50 text-indigo-600 px-3 py-1.5 rounded-full hover:bg-indigo-100 transition-colors flex-shrink-0"
                            >
                              <MapPin className="w-3.5 h-3.5" />
                              <span className="text-[11px] font-bold whitespace-nowrap">식당 찾기</span>
                            </a>
                          </div>

                          {rec.restaurant_name && (
                            <div className="mb-4 p-3 bg-slate-50 rounded-xl border border-slate-100/80 shadow-sm">
                              <p className="text-[12px] font-bold text-slate-800 flex items-center mb-1">
                                <span className="mr-1.5 text-[10px]">🏪</span> {rec.restaurant_name}
                              </p>
                              <p className="text-[10px] text-slate-500 leading-snug line-clamp-2">
                                {rec.restaurant_info}
                              </p>
                            </div>
                          )}
                          
                          <div className="grid grid-cols-3 gap-2 mt-4 text-center">
                            <div className="bg-slate-50 p-2 rounded-xl">
                              <span className="block text-[9px] font-bold text-slate-400 uppercase">단백질</span>
                              <span className="text-xs font-bold text-slate-700">{rec.protein}g</span>
                            </div>
                            <div className="bg-slate-50 p-2 rounded-xl">
                              <span className="block text-[9px] font-bold text-slate-400 uppercase">탄수화물</span>
                              <span className="text-xs font-bold text-slate-700">{rec.carbs}g</span>
                            </div>
                            <div className="bg-slate-50 p-2 rounded-xl">
                              <span className="block text-[9px] font-bold text-slate-400 uppercase">지방</span>
                              <span className="text-xs font-bold text-slate-700">{rec.fat}g</span>
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        <style jsx global>{`
          .no-scrollbar::-webkit-scrollbar {
            display: none;
          }
          .no-scrollbar {
            -ms-overflow-style: none;
            scrollbar-width: none;
          }
          
          /* Custom Chrome outline fix */
          input[type="number"]::-webkit-inner-spin-button,
          input[type="number"]::-webkit-outer-spin-button {
            -webkit-appearance: none;
            margin: 0;
          }
        `}</style>
      </main>
    </div>
  );
}
