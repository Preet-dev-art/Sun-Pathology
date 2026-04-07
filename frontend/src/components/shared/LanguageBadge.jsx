// src/components/shared/LanguageBadge.jsx

const LABELS = { en: "English", hi: "हिंदी", gu: "ગુજરાતી" };

export default function LanguageBadge({ language }) {
  if (!language) return null;
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-sun-blue">
      {LABELS[language] || language}
    </span>
  );
}