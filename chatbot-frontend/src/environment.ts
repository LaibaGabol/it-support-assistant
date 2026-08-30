import type { EnvironmentInfo } from "./types";

// Capture ONLY the browser fields listed below. No cookies, no storage
// contents, no other browser data are read.
export function captureEnvironment(): EnvironmentInfo {
  return {
    user_agent: navigator.userAgent,
    screen_resolution: `${window.screen.width}x${window.screen.height}`,
    viewport: `${window.innerWidth}x${window.innerHeight}`,
    language: navigator.language,
    timestamp: new Date().toISOString(),
    os: navigator.platform,
  };
}
