"use client";

export const checkoutSessionKey = "tickete-checkout-session";
export const checkoutSessionEvent = "tickete-checkout-session-changed";

export function checkoutEpoch() {
  return localStorage.getItem(checkoutSessionKey) || "initial";
}

export function clearCheckoutAccess() {
  for (const key of Object.keys(sessionStorage)) {
    if (key.startsWith("tickete-checkout-")) sessionStorage.removeItem(key);
  }
}

export function changeCheckoutSession() {
  clearCheckoutAccess();
  // Only a random generation marker is shared between tabs, never order tokens.
  localStorage.setItem(checkoutSessionKey, crypto.randomUUID());
  window.dispatchEvent(new Event(checkoutSessionEvent));
}
