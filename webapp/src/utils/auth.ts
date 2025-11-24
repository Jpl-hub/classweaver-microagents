import { computed, ref } from "vue";
import { fetchCurrentUser, loginUser, logoutUser, primeCsrfToken, registerUser } from "../services/api";
import type { UserProfile } from "../types";

export const STORAGE_KEY = "classweaver:current-user";
const currentUser = ref<UserProfile | null>(null);
const authLoading = ref(false);
const initialized = ref(false);
const authError = ref<string | null>(null);

function persistUser(user: UserProfile | null) {
  if (typeof window === "undefined") return;
  if (user) {
    window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(user));
  } else {
    window.sessionStorage.removeItem(STORAGE_KEY);
  }
}

function restoreUser() {
  if (typeof window === "undefined") return;
  if (currentUser.value) return;
  try {
    const raw = window.sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return;
    const parsed = JSON.parse(raw) as UserProfile;
    if (parsed?.id) {
      currentUser.value = parsed;
      initialized.value = true;
    }
  } catch {
    window.sessionStorage.removeItem(STORAGE_KEY);
  }
}

async function loadCurrentUser(force = false): Promise<UserProfile | null> {
  restoreUser();
  if (authLoading.value || (initialized.value && !force)) {
    return currentUser.value;
  }
  authLoading.value = true;
  authError.value = null;
  try {
    await primeCsrfToken();
    const user = await fetchCurrentUser();
    currentUser.value = user;
    persistUser(user);
  } catch (error) {
    const status = (error as any)?.status;
    if (status === 401) {
      currentUser.value = null;
      persistUser(null);
    } else if (!currentUser.value) {
      currentUser.value = null;
      persistUser(null);
    }
  } finally {
    authLoading.value = false;
    initialized.value = true;
  }
  return currentUser.value;
}

async function signIn(payload: { username: string; password: string }): Promise<UserProfile> {
  authLoading.value = true;
  authError.value = null;
  try {
    const user = await loginUser(payload);
    currentUser.value = user;
    persistUser(user);
    initialized.value = true;
    return user;
  } catch (error) {
    const message = error instanceof Error ? error.message : "登录失败，请重试。";
    authError.value = message;
    currentUser.value = null;
    initialized.value = true;
    throw error;
  } finally {
    authLoading.value = false;
  }
}

async function signUp(payload: { username: string; password: string; email?: string }): Promise<UserProfile> {
  authLoading.value = true;
  authError.value = null;
  try {
    const user = await registerUser(payload);
    currentUser.value = user;
    persistUser(user);
    initialized.value = true;
    return user;
  } catch (error) {
    const message = error instanceof Error ? error.message : "注册失败，请重试。";
    authError.value = message;
    currentUser.value = null;
    initialized.value = true;
    throw error;
  } finally {
    authLoading.value = false;
  }
}

async function signOut(): Promise<void> {
  try {
    await logoutUser();
  } finally {
    currentUser.value = null;
    persistUser(null);
  }
}

export function useAuth() {
  return {
    currentUser,
    isAuthenticated: computed(() => Boolean(currentUser.value)),
    authLoading,
    authError,
    loadCurrentUser,
    signIn,
    signUp,
    signOut,
  };
}
