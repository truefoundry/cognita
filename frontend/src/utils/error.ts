import notify from "@/components/base/molecules/Notify";


export function notifyError(baseMessage: string, err?: any, defaultMessage? : string) {
  const message =
  err?.message ||
  err?.data?.error ||
    err?.error ||
    err?.details?.msg || (typeof err?.data?.detail === 'string' && err?.data?.detail) || defaultMessage;

  notify('error', baseMessage, message);
}
