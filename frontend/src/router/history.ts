import { createBrowserHistory } from 'history'

const history = createBrowserHistory({ window })

export default {
  ...history,
  replace: (to: string, state?: any) => {
    const locationState = history.location.state as any
    history.replace(to, {
      ...(state ?? {}),
      drawerBackRequired: locationState?.drawerBackRequired,
      breadcrumbsBackButton: locationState?.breadcrumbsBackButton,
    })
  },
}
