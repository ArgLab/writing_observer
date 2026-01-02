import { useState, useRef, useEffect } from "react";
import { ChevronDown, Filter } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const essayTypes = [
  "Argumentative",
  "Narrative",
  "Personal",
  "Analytical",
  "Reflective",
  "Opinion",
  "Education",
  "Descriptive",
  "Experience",
  "Economics",
  "Research",
];

export default function TypeFilterDropdown({ selectedTypes, setSelectedTypes }) {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  const toggleType = (type) => {
    setSelectedTypes((prev) =>
      prev.includes(type) ? prev.filter((t) => t !== type) : [...prev, type]
    );
  };

  const handleClearAll = () => {
    setSelectedTypes([]);
  };

  // Close on outside click
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div ref={dropdownRef} className="relative w-full sm:w-120">
      {/* Toggle Button */}
      <button
        onClick={() => setIsDropdownOpen((prev) => !prev)}
        className="flex justify-between items-center w-full border border-gray-300 rounded-md px-3 py-2 text-sm text-gray-700 bg-white shadow-sm focus:ring-2 focus:ring-blue-500 focus:outline-none h-[48px] overflow-hidden text-ellipsis whitespace-nowrap"
        title={selectedTypes.join(", ")}
      >
        <span className="truncate">
          {selectedTypes.length === 0 ? (
            <span className="font-normal flex gap-2 items-center"><Filter /> Filter essay types</span>
          ) : (
            <>
              <span className="font-semibold">Filtered Types:</span>{" "}
              {selectedTypes.join(", ")}
            </>
          )}
        </span>
        <ChevronDown className="w-4 h-4 ml-2 text-gray-500 shrink-0" />
      </button>

      {/* Dropdown Panel with Animation */}
      <AnimatePresence>
        {isDropdownOpen && (
          <motion.div
            key="dropdown"
            initial={{ opacity: 0, y: -6 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ duration: 0.15 }}
            className="absolute z-10 mt-2 w-full bg-white border border-gray-200 rounded-md shadow-lg max-h-60 overflow-y-auto"
          >
            <div className="p-2">
              <button
                onClick={handleClearAll}
                className="text-sm text-red-500 hover:text-red-700 underline mb-2"
              >
                Clear All
              </button>

              {essayTypes.map((type) => (
                <label
                  key={type}
                  className="flex items-center px-2 py-2 text-sm text-gray-700 hover:bg-gray-50 cursor-pointer rounded"
                >
                  <input
                    type="checkbox"
                    checked={selectedTypes.includes(type)}
                    onChange={() => toggleType(type)}
                    className="mr-2 w-4 h-4 accent-blue-600"
                  />
                  {type}
                </label>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
