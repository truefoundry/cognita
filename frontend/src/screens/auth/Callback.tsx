import React from 'react'

type Props = {}
import { useEffect } from 'react';
import history from '@/router/history';
import { login } from '@/stores/UserInfo';
import { useDispatch } from 'react-redux';

const Callback = () => {
  const dispatch = useDispatch()

  useEffect(() => {
    // Retrieve the authorization code from the URL query parameters
    const urlParams = new URLSearchParams(window.location.search);
    const accessToken = urlParams.get('access_token');
    const customerId = urlParams.get('user');

    if (accessToken && customerId) {
      // Store the access token in the session storage
      dispatch(login({ accessToken, customerId }));
    } else {
      // Redirect to the login page
      history.push('/login');
    }
  }, [history]);

  return (
    <div>
      <p>Please wait logging you in...</p>
    </div>
  );
};

export default Callback
