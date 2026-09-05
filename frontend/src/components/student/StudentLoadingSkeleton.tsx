/**
 * PEVN Frontend — Student Portal Loading Skeletons
 *
 * Smooth placeholder skeleton blocks for cards, metrics, and lists.
 */

import React from 'react'

export const StudentLoadingSkeleton: React.FC<{ count?: number; type?: 'metrics' | 'cards' | 'table' }> = ({
  count = 4,
  type = 'cards',
}) => {
  const shimmerStyle: React.CSSProperties = {
    backgroundColor: '#F1F5F9',
    borderRadius: '8px',
    animation: 'pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
  }

  if (type === 'metrics') {
    return (
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '1rem',
          marginBottom: '1.5rem',
        }}
      >
        {Array.from({ length: count }).map((_, i) => (
          <div
            key={i}
            style={{
              backgroundColor: '#FFFFFF',
              borderRadius: '12px',
              border: '1px solid #E2E8F0',
              padding: '1.25rem',
              height: '120px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <div style={{ ...shimmerStyle, width: '40px', height: '40px', borderRadius: '10px' }} />
              <div style={{ ...shimmerStyle, width: '60px', height: '20px' }} />
            </div>
            <div>
              <div style={{ ...shimmerStyle, width: '80px', height: '24px', marginBottom: '0.4rem' }} />
              <div style={{ ...shimmerStyle, width: '120px', height: '16px' }} />
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (type === 'table') {
    return (
      <div
        style={{
          backgroundColor: '#FFFFFF',
          borderRadius: '12px',
          border: '1px solid #E2E8F0',
          padding: '1.5rem',
        }}
      >
        <div style={{ ...shimmerStyle, width: '200px', height: '24px', marginBottom: '1.25rem' }} />
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {Array.from({ length: count }).map((_, i) => (
            <div
              key={i}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '1rem 0',
                borderBottom: '1px solid #F1F5F9',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <div style={{ ...shimmerStyle, width: '36px', height: '36px', borderRadius: '8px' }} />
                <div>
                  <div style={{ ...shimmerStyle, width: '180px', height: '18px', marginBottom: '0.35rem' }} />
                  <div style={{ ...shimmerStyle, width: '120px', height: '14px' }} />
                </div>
              </div>
              <div style={{ ...shimmerStyle, width: '80px', height: '24px' }} />
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
        gap: '1.25rem',
      }}
    >
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          style={{
            backgroundColor: '#FFFFFF',
            borderRadius: '12px',
            border: '1px solid #E2E8F0',
            padding: '1.25rem',
            height: '180px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
          }}
        >
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
              <div style={{ ...shimmerStyle, width: '100px', height: '20px' }} />
              <div style={{ ...shimmerStyle, width: '70px', height: '20px' }} />
            </div>
            <div style={{ ...shimmerStyle, width: '85%', height: '22px', marginBottom: '0.5rem' }} />
            <div style={{ ...shimmerStyle, width: '60%', height: '16px' }} />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ ...shimmerStyle, width: '110px', height: '16px' }} />
            <div style={{ ...shimmerStyle, width: '90px', height: '32px', borderRadius: '6px' }} />
          </div>
        </div>
      ))}
    </div>
  )
}
