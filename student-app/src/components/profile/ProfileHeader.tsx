'use client';

import { UserResponse } from '@/lib/api/auth';

interface ProfileHeaderProps {
  user: UserResponse;
  className?: string;
}

export function ProfileHeader({ user, className = '' }: ProfileHeaderProps) {
  const initials = `${user.first_name?.[0] || ''}${user.last_name?.[0] || ''}`.toUpperCase();

  return (
    <div className={`flex items-center gap-4 ${className}`}>
      {/* Avatar */}
      {user.avatar_url ? (
        <img
          src={user.avatar_url}
          alt={`${user.first_name} ${user.last_name}`}
          className="h-20 w-20 rounded-full object-cover ring-4 ring-primary/20"
        />
      ) : (
        <div className="flex h-20 w-20 items-center justify-center rounded-full bg-primary/10 text-2xl font-bold text-primary ring-4 ring-primary/20">
          {initials || '?'}
        </div>
      )}

      {/* User Info */}
      <div className="flex-1 min-w-0">
        <h1 className="text-xl font-bold text-foreground truncate">
          {user.first_name} {user.last_name}
        </h1>
        {user.middle_name && (
          <p className="text-sm text-muted-foreground truncate">{user.middle_name}</p>
        )}
        <p className="text-sm text-muted-foreground truncate">{user.email}</p>
      </div>
    </div>
  );
}
