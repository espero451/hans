import { ref } from "vue"
import { getCurrentUser, logout } from "../api/auth"

const user = ref<any | null>(null)

export function useAuth() {
  function setUser(u: any) {
    user.value = u
  }

  function clearUser() {
    user.value = null
  }

  async function loadUser() {
    const token = localStorage.getItem("token")
    if (!token) {
      user.value = null
      return null
    }
    try {
      const currentUser = await getCurrentUser()
      user.value = currentUser
      return currentUser
    } catch (err) {
      logout()
      user.value = null
      throw err
    }
  }

  return {
    user,
    setUser,
    clearUser,
    loadUser,
  }
}
