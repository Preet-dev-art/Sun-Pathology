// src/pages/VoicePage.jsx 

import { useSession } from "../hooks/useSession";
import { useCallSession } from "../hooks/useCallSession";
import CallScreen from "../components/Voice/CallScreen";

export default function VoicePage() {
  const { sessionId } = useSession();

  const {
    callState,
    transcript,
    sheetalText,
    messages,
    language,
    callDuration,
    error,
    startCall,
    endCall,
  } = useCallSession({ sessionId });

  return (
    <div className="flex flex-col flex-1 h-[calc(100vh-64px)]">
      <CallScreen
        callState={callState}
        transcript={transcript}
        sheetalText={sheetalText}
        messages={messages}
        language={language}
        callDuration={callDuration}
        error={error}
        onStartCall={startCall}
        onEndCall={endCall}
      />
    </div>
  );
}