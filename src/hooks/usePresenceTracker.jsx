import { useEffect, useRef } from 'react';
import { useAuth } from './useAuth';
import { getApiUrl } from '../services/api';

/**
 * Frequency of presence heartbeat pings to the server.
 * Default: 60 seconds (well within server's 120-second timeout threshold).
 */
const HEARTBEAT_INTERVAL_MS = 60000;

/**
 * Minimum throttle duration between updating the local activity ref timestamp (in ms).
 * Prevents unnecessary new Date() allocations on continuous high-frequency mousemove/scroll.
 */
const ACTIVITY_THROTTLE_MS = 3000;

/**
 * usePresenceTracker Hook
 *
 * Lightweight client-side presence & activity tracker:
 * - Only operates when authenticated with valid JWT token and server-issued sessionId.
 * - Captures user interaction events locally via lightweight window listeners without triggering React re-renders.
 * - Periodically transmits heartbeat pings with latest ISO-8601 activity timestamp.
 * - Safely handles network drops or backend downtime without logging the user out.
 * - Fully cleans up intervals and event listeners on unmount or user logout.
 */
export const usePresenceTracker = () => {
  const { user, isAuthenticated } = useAuth();

  // Local activity timestamp ref — updated on user interaction without React state re-renders
  const lastActivityRef = useRef(new Date().toISOString());
  const lastEventThrottleRef = useRef(0);

  useEffect(() => {
    const token = user?.token;
    const sessionId = user?.sessionId;

    // Do NOT operate if not authenticated or missing required session/token credentials
    if (!isAuthenticated || !token || !sessionId) {
      return;
    }

    // Initialize local activity with current time upon entering authenticated session
    lastActivityRef.current = new Date().toISOString();
    lastEventThrottleRef.current = Date.now();

    /**
     * Throttled user activity handler.
     * Updates the ref timestamp without causing React component re-renders.
     */
    const handleUserActivity = () => {
      const now = Date.now();
      if (now - lastEventThrottleRef.current >= ACTIVITY_THROTTLE_MS) {
        lastEventThrottleRef.current = now;
        lastActivityRef.current = new Date(now).toISOString();
      }
    };

    // Attach passive listeners for all primary user interaction types
    const events = ['mousemove', 'mousedown', 'keydown', 'touchstart', 'scroll', 'click'];
    events.forEach((evt) => {
      window.addEventListener(evt, handleUserActivity, { passive: true });
    });

    /**
     * Transmits heartbeat ping to the backend presence endpoint.
     */
    const sendHeartbeat = async () => {
      try {
        await fetch(getApiUrl('/presence/heartbeat'), {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({
            sessionId,
            lastActivityAt: lastActivityRef.current
          })
        });
      } catch (err) {
        // Heartbeat failure must NOT log the user out; suppress error to avoid disrupting UX
        console.warn('[PresenceTracker] Heartbeat sync deferred:', err?.message || err);
      }
    };

    // Trigger initial heartbeat shortly after session initialization
    const initialTimer = setTimeout(() => {
      sendHeartbeat();
    }, 2000);

    // Set recurring heartbeat interval
    const intervalId = setInterval(sendHeartbeat, HEARTBEAT_INTERVAL_MS);

    // Cleanup: remove listeners and timers on unmount or when authentication state terminates
    return () => {
      clearTimeout(initialTimer);
      clearInterval(intervalId);
      events.forEach((evt) => {
        window.removeEventListener(evt, handleUserActivity);
      });
    };
  }, [isAuthenticated, user?.sessionId, user?.token]);

  return {
    getLastActivity: () => lastActivityRef.current
  };
};

export default usePresenceTracker;
