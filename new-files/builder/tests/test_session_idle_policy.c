/* Host-side tests for the independent session deadline; no ESP hardware needed. */
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>

#include "../ports/esp32/display_manager/session_idle_policy.h"

int main(void) {
    session_idle_policy_t s = {0, 1800000, false, false};
    assert(!session_idle_expired(&s, 99999999));
    session_idle_arm(&s, 1000);
    assert(!session_idle_expired(&s, 1800999));
    assert(session_idle_expired(&s, 1801000));

    session_idle_activity(&s, 1800999);
    assert(!session_idle_expired(&s, 1801000));
    assert(session_idle_expired(&s, 3600999));

    /* Re-arming while editing/validating a seed must not reset the timer. */
    session_idle_arm(&s, 3000000);
    assert(s.last_activity_ms == 1800999);

    const uint32_t limits[] = {300000, 900000, 1800000, 3600000};
    for (unsigned i = 0; i < sizeof(limits) / sizeof(limits[0]); ++i) {
        session_idle_set_timeout(&s, limits[i], 5000);
        assert(!session_idle_expired(&s, 5000 + limits[i] - 1));
        assert(session_idle_expired(&s, 5000 + limits[i]));
    }

    /* "No limit" disables expiry even when armed; selecting a limit again
     * starts a fresh interval. */
    session_idle_set_timeout(&s, 0, 5000);
    assert(!session_idle_expired(&s, UINT64_MAX));
    session_idle_set_timeout(&s, 300000, 6000);
    assert(!session_idle_expired(&s, 305999));
    assert(session_idle_expired(&s, 306000));

    session_idle_set_paused(&s, true, 6000);
    assert(!session_idle_expired(&s, 99999999));
    session_idle_set_paused(&s, false, 100000000);
    assert(!session_idle_expired(&s, 100000000 + s.timeout_ms - 1));
    assert(session_idle_expired(&s, 100000000 + s.timeout_ms));
    assert(!session_idle_expired(&s, 1)); /* monotonic clock guard */
    puts("Session idle policy tests passed");
    return 0;
}