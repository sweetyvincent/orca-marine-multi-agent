import React, { useState, useRef, useEffect } from 'react';
import { MapPin, ChevronDown } from 'lucide-react';

const PRESET_LOCATIONS = [
  'Chennai', 'Mumbai', 'Gulf of Mexico', 'California Coast',
  'Chesapeake Bay', 'Florida Keys', 'Great Barrier Reef', 'North Sea'
];

export default function LocationPicker({ value, onChange }) {
  const [isOpen, setIsOpen] = useState(false);
  const [isCustom, setIsCustom] = useState(false);
  const containerRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <div className="relative flex items-center" ref={containerRef}>
      <div 
        className="flex items-center bg-ocean-900/50 border border-ocean-700/50 rounded-lg px-3 py-3 cursor-pointer hover:bg-ocean-800/50 transition-colors"
        onClick={() => setIsOpen(!isOpen)}
      >
        <MapPin className="w-4 h-4 text-ocean-400 mr-2 flex-shrink-0" />
        <span className="text-sm truncate w-24 md:w-32 text-ocean-100">{value || 'Select Location'}</span>
        <ChevronDown className="w-4 h-4 text-ocean-400 ml-2 flex-shrink-0" />
      </div>

      {isOpen && (
        <div className="absolute bottom-full mb-2 left-0 w-48 bg-ocean-900 border border-ocean-700 rounded-lg shadow-xl overflow-hidden z-20">
          <div className="max-h-60 overflow-y-auto">
            {PRESET_LOCATIONS.map(loc => (
              <div 
                key={loc}
                className="px-4 py-2 hover:bg-ocean-700 text-sm text-ocean-100 cursor-pointer"
                onClick={() => {
                  onChange(loc);
                  setIsCustom(false);
                  setIsOpen(false);
                }}
              >
                {loc}
              </div>
            ))}
            <div 
              className="px-4 py-2 hover:bg-ocean-700 text-sm text-ocean-300 font-medium cursor-pointer border-t border-ocean-800"
              onClick={() => {
                setIsCustom(true);
                setIsOpen(false);
              }}
            >
              Custom...
            </div>
          </div>
        </div>
      )}
      
      {isCustom && !isOpen && (
        <div className="absolute left-0 bottom-full mb-2 z-20 bg-ocean-900 p-2 rounded-lg border border-ocean-700 shadow-xl">
          <input 
            type="text" 
            autoFocus
            placeholder="Type location..."
            value={value}
            onChange={(e) => onChange(e.target.value)}
            className="w-48 bg-ocean-950 border border-ocean-600 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-ocean-400"
            onKeyDown={(e) => {
              if (e.key === 'Enter') setIsCustom(false);
            }}
          />
          <button onClick={() => setIsCustom(false)} className="text-xs text-ocean-400 mt-2 hover:text-ocean-200">Done</button>
        </div>
      )}
    </div>
  );
}
