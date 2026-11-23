#ifndef SESSION_IDLE_POLICY_H
#define SESSION_IDLE_POLICY_H

#include <stdbool.h>
#include <stdint.h>

/* Pure timing policy. Caller serializes access and supplies a monotonic clock. */
typedef struct {
    uint64_t last_activity_ms;
    uint32_t timeout_ms;
    bool armed;
    bool paused;
} session_idle_policy_t;

static inline void session_idle_activity(session_idle_policy_t *s, uint64_t now_ms) {
    s->last_activity_ms = now_ms;
}

static inline void session_idle_arm(session_idle_policy_t *s, uint64_t now_ms) {
    if (s->armed) return;
    s->armed = true;
    session_idle_activity(s, now_ms);
}

static inline void session_idle_set_timeout(session_idle_policy_t *s, uint32_t timeout_ms,
                                            uint64_t now_ms) {
    s->timeout_ms = timeout_ms;
    session_idle_activity(s, now_ms);
}

static inline void session_idle_set_paused(session_idle_policy_t *s, bool paused,
                                           uint64_t now_ms) {
    s->paused = paused;
    /* A full new interval after the protected operation completes. */
    session_idle_activity(s, now_ms);
}

static inline bool session_idle_expired(const session_idle_policy_t *s, uint64_t now_ms) {
    return s->armed && !s->paused && s->timeout_ms && now_ms >= s->last_activity_ms &&
           now_ms - s->last_activity_ms >= s->timeout_ms;
}

#endif