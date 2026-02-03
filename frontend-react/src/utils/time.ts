export function getMarketStatus(): "open" | "closed" {
  const now = new Date();
  const utc = now.getTime() + now.getTimezoneOffset() * 60000;
  const est = new Date(utc - 5 * 3600 * 1000);
  const day = est.getDay();
  const hours = est.getHours() + est.getMinutes() / 60;
  const isWeekday = day >= 1 && day <= 5;
  const isOpen = isWeekday && hours >= 9.5 && hours <= 16;
  return isOpen ? "open" : "closed";
}
