/**
 * PEVN Frontend — Guardian Loading Skeleton Component
 *
 * Polished skeleton placeholders during asynchronous data fetching in the Guardian Portal.
 */

import React from 'react'

export const GuardianLoadingSkeleton: React.FC<{ type?: 'cards' | 'table' | 'overview' }> = ({
  type = 'cards',
}) => {
  if (type === 'overview') {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <div
          style={{
            height: '70px',
            backgroundColor: '#F1F5F9',
            borderRadius: '12px',
            animation: 'pulse 1.5s infinite ease-in-out',
          }}
        />

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
            gap: '1rem',
          }}
        >
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              style={{
                height: '100px',
                backgroundColor: '#F1F5F9',
                borderRadius: '14px',
                animation: 'pulse 1.5s infinite ease-in-out',
              }}
            />
          ))}
        </div>

        <div
          style={{
            height: '240px',
            backgroundColor: '#F1F5F9',
            borderRadius: '14px',
            animation: 'pulse 1.5s infinite ease-in-out',
          }}
        />
      </div>
    )
  }

  if (type === 'table') {
    return (
      <div
        style={{
          backgroundColor: '#FFFFFF',
          borderRadius: '14px',
          border: '1px solid #E2E8F0',
          padding: '1.5rem',
        }}
      >
        <div
          style={{
            height: '35px',
            backgroundColor: '#F1F5F9',
            borderRadius: '8px',
            marginBottom: '1rem',
            animation: 'pulse 1.5s infinite ease-in-out',
          }}
        />
        {[1, 2, 3, 4, 5].map((i) => (
          <div
            key={i}
            style={{
              height: '48px',
              backgroundColor: '#F8FAFC',
              borderRadius: '6px',
              marginBottom: '0.5rem',
              animation: 'pulse 1.5s infinite ease-in-out',
            }}
          />
        ))}
      </div>
    )
  }

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
        gap: '1.25rem',
      }}
    >
      {[1, 2, 3, 4, 5, 6].map((i) => (
        <div
          key={i}
          style={{
            height: '180px',
            backgroundColor: '#F1F5F9',
            borderRadius: '14px',
            animation: 'pulse 1.5s infinite ease-in-out',
          }}
        />
      ))}
    </div>
  )
}
