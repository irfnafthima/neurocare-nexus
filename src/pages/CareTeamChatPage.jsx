import React from 'react';
import { useAuth } from '../hooks/useAuth';
import { useToast } from '../components/common/Toast';
import { CareTeamChat } from '../components/chat/CareTeamChat';
import { getApiUrl } from '../services/api';

export const CareTeamChatPage = () => {
  const { user, authFetch } = useAuth();
  const { addToast } = useToast();

  return (
    <div className="max-w-7xl mx-auto">
      <CareTeamChat 
        user={user} 
        authFetch={authFetch} 
        getApiUrl={getApiUrl} 
        addToast={addToast} 
      />
    </div>
  );
};

export default CareTeamChatPage;
