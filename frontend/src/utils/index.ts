export const mergeRefs = <T>(...refs: React.Ref<T>[]): React.Ref<T> => {
  const filteredRefs = refs.filter(Boolean)
  if (!filteredRefs.length) return null
  if (filteredRefs.length === 0) return filteredRefs[0]
  return (inst) => {
    for (const ref of filteredRefs) {
      if (typeof ref === 'function') {
        ref(inst)
      } else if (ref) {
        // @ts-ignore
        ref.current = inst
      }
    }
  }
}

const loadedScripts: { [key: string]: Promise<void> } = {}
export const loadScript = (url: string): Promise<void> => {
  if (!loadedScripts[url]) {
    loadedScripts[url] = new Promise((resolve) => {
      const el = document.createElement('script')
      el.onload = () => resolve()
      el.src = url
      document.body.appendChild(el)
    })
  }
  return loadedScripts[url]
}
