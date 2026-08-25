/**
 * PEVN Frontend — Tabs Navigation Component
 *
 * Tab navigation bar for academic views and sub-module switching.
 */

import React from 'react'

export interface TabItem {
  id: string
  label: string
  icon?: string
  badge?: number | string
}

export interface TabsProps {
  tabs: TabItem[]
  activeTab: string
  onChange: (tabId: string) => void
}

export const Tabs: React.FC<TabsProps> = ({ tabs, activeTab, onChange }) => {
  return (
    <div
      style={{
        display: 'flex',
        gap: '0.5rem',
        borderBottom: '2px solid #E2E8F0',
        paddingBottom: '0.25rem',
        marginBottom: '1.5rem',
        overflowX: 'auto',
      }}
      role="tablist"
      aria-label="Pestañas de navegación académica"
    >
      {tabs.map((tab) => {
        const isActive = tab.id === activeTab
        return (
          <button
            key={tab.id}
            role="tab"
            aria-selected={isActive}
            onClick={() => {
              onChange(tab.id)
            }}
            style={{
              padding: '0.625rem 1rem',
              border: 'none',
              background: 'none',
              cursor: 'pointer',
              fontSize: '0.875rem',
              fontWeight: isActive ? 700 : 500,
              color: isActive ? '#1E40AF' : '#64748B',
              borderBottom: isActive ? '3px solid #1E40AF' : '3px solid transparent',
              marginBottom: '-0.35rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              whiteSpace: 'nowrap',
              transition: 'all 150ms ease-in-out',
            }}
          >
            {tab.icon && <span>{tab.icon}</span>}
            <span>{tab.label}</span>
            {tab.badge !== undefined && (
              <span
                style={{
                  fontSize: '0.75rem',
                  padding: '0.1rem 0.4rem',
                  borderRadius: '9999px',
                  backgroundColor: isActive ? '#DBEAFE' : '#F1F5F9',
                  color: isActive ? '#1E40AF' : '#64748B',
                  fontWeight: 600,
                }}
              >
                {tab.badge}
              </span>
            )}
          </button>
        )
      })}
    </div>
  )
}

export default Tabs
