import {
  SideNav,
  SideNavItems,
  SideNavLink,
} from '@carbon/react';
import {
  Dashboard,
  ChartLine,
  DocumentTasks,
  Settings,
} from '@carbon/icons-react';

export default function CarbonSideNav({ activeItem, onItemClick, isExpanded, onToggle }) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Dashboard },
    { id: 'analytics', label: 'Analytics', icon: ChartLine },
    { id: 'history', label: 'Trade History', icon: DocumentTasks },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  return (
    <SideNav
      aria-label="Side navigation"
      expanded={isExpanded}
      isPersistent={false}
      onOverlayClick={onToggle}
    >
      <SideNavItems>
        {navItems.map(({ id, label, icon: Icon }) => (
          <SideNavLink
            key={id}
            renderIcon={Icon}
            isActive={activeItem === id}
            onClick={() => onItemClick(id)}
          >
            {label}
          </SideNavLink>
        ))}
      </SideNavItems>
    </SideNav>
  );
}
