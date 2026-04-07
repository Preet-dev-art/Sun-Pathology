// src/components/shared/SheetalAvatar.jsx

export default function SheetalAvatar({ size = 48, speaking = false }) {
  return (
    <div
      className={`relative rounded-full bg-gradient-to-br from-sun-sky to-sun-blue flex items-center justify-center text-white font-bold select-none
        ${speaking ? "ring-4 ring-sun-sky ring-opacity-50 animate-pulse" : ""}
      `}
      style={{ width: size, height: size, fontSize: size * 0.35 }}
    >
      SH
      {speaking && (
        <span className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-400 rounded-full border-2 border-white" />
      )}
    </div>
  );
}