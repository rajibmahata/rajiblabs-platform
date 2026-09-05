/* Admin toast bus — any admin page can fire: toast("Title", "message"). */
export function toast(title: string, msg: string) {
  window.dispatchEvent(new CustomEvent("rla-toast", { detail: { title, msg } }));
}
