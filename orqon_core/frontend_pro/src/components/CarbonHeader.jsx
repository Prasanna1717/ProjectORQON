import {
  Header,
  HeaderName,
  HeaderGlobalBar,
  HeaderGlobalAction,
} from '@carbon/react';
import { UserAvatar, Notification } from '@carbon/icons-react';

export default function CarbonHeader({ platformName, userName }) {
  return (
    <Header aria-label={platformName}>
      <HeaderName href="#" prefix="IBM">
        {platformName}
      </HeaderName>
      
      <HeaderGlobalBar>
        <HeaderGlobalAction
          aria-label="Notifications"
          tooltipAlignment="end"
        >
          <Notification size={20} />
        </HeaderGlobalAction>
        
        <HeaderGlobalAction
          aria-label="User Profile"
          tooltipAlignment="end"
        >
          <UserAvatar size={20} />
        </HeaderGlobalAction>
      </HeaderGlobalBar>
    </Header>
  );
}
