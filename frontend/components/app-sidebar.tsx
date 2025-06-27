'use client';

import { useRouter } from 'next/navigation';

import { PlusIcon } from '@/components/icons';
import { SidebarHistory } from '@/components/sidebar-history';
import { Button } from '@/components/ui/button';
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  useSidebar,
} from '@/components/ui/sidebar';
import Link from 'next/link';
import { Tooltip, TooltipContent, TooltipTrigger } from './ui/tooltip';
import { useQueryLoading } from '@/hooks/use-query-loading';

export function AppSidebar() {
  const router = useRouter();
  const { setOpenMobile } = useSidebar();
  const { setQueryLoading } = useQueryLoading();

  return (
    <Sidebar className="group-data-[side=left]:border-r-0 bg-sidebar">
      <SidebarHeader>
        <SidebarMenu>
          <div className="flex flex-row justify-between items-center">
            <Link
              href="/"
              onClick={() => {
                // Go to financialdatasets.ai
                window.location.href = 'https://financialdatasets.ai';
                setOpenMobile(false);
              }}
              className="flex flex-row gap-3 items-center"
            >
            <span className="bg-clip-text text-xl font-bold px-2 text-primary">
              financial datasets
            </span>
            </Link>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  type="button"
                  className="p-2 h-fit"
                  onClick={() => {
                    setOpenMobile(false);
                    setQueryLoading(false, []);
                    router.push('/');
                    router.refresh();
                  }}
                >
                  <PlusIcon />
                </Button>
              </TooltipTrigger>
              <TooltipContent align="end">New Chat</TooltipContent>
            </Tooltip>
          </div>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <SidebarHistory />
      </SidebarContent>
      <SidebarFooter>
        {/* Footer content if needed */}
      </SidebarFooter>
    </Sidebar>
  );
}
